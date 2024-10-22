from django.contrib.auth import authenticate
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from edms.assets.models import Asset
from edms.assets.serializers import AssetSerializer
from edms.common.upload_helper import validate_file_type
from edms.organization.models import OrganizationUnit
from edms.users.models import User, UserSignature


class UpdateUserSignatureSerializer(serializers.ModelSerializer):
    signature_images = serializers.ListField(
        required=True,
        child=serializers.FileField(),
    )
    is_default = serializers.BooleanField(
        required=False,
        default=False
    )

    class Meta:
        model = User
        fields = [
            "signature_images",
            "is_default"
        ]

    def validate(self, data):
        signature_images = data.get('signature_images', [])
        if len(signature_images) > 1:
            raise serializers.ValidationError(
                {"detail": "You can only include one signature image."},
            )

        for image in signature_images:
            allowed_extensions = ["png", "jpeg", "jpg"]
            validate_file_type(image, allowed_extensions)
        return data

    def update(self, instance, validated_data):
        signature_images = validated_data.pop('signature_images', [])
        is_default = validated_data.pop('is_default', False)

        instance.create_signature_image(signature_images[0], Asset.SIGNATURE_IMAGE, is_default)

        return instance


class UserSignatureSerializer(serializers.ModelSerializer):
    signature_image = AssetSerializer(read_only=True)

    class Meta:
        model = UserSignature
        fields = ["signature_image", "is_default"]


class UserSerializer(serializers.ModelSerializer[User]):
    role = serializers.CharField(
        read_only=True
    )

    signature_images = UserSignatureSerializer(
        required=False,
        many=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "phone_number",
            "organization_unit",
            "department",
            "position",
            "gender",
            "external_user_id",
            "citizen_identification",
            "signature_images",
            "role"
            # "url",
        ]

        # extra_kwargs = {
        #     "url": {"view_name": "user-detail", "lookup_field": "pk"},
        # }

    def to_representation(self, instance):
        request = self.context.get('request', None)
        data = super().to_representation(instance)
        data["role"] = "admin" if instance.is_superuser or instance.is_staff else "staff"
        data["signature_images"] = UserSignatureSerializer(
            instance.user_signature_entries.all(),
            many=True,
            context=self.context
        ).data
        return data


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        required=False,
        write_only=True,
        allow_blank=False,
        allow_null=True,
    )
    email = serializers.CharField(
        required=True,
        max_length=150,
        min_length=3,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length",
        },
    )
    name = serializers.CharField(
        required=True,
        max_length=150,
        min_length=1,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length",
        },
    )
    citizen_identification = serializers.CharField(
        required=True,
        max_length=15,
        min_length=10,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length",
        },
    )
    external_user_id = serializers.CharField(
        required=False,
        max_length=15,
        min_length=10,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length",
        },
    )
    phone_number = serializers.CharField(
        required=True,
        max_length=15,
        min_length=10,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length",
        },
    )
    organization_unit = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationUnit.objects.all(),
        required=False,
        allow_null=True,
    )
    department = serializers.CharField(required=True)
    position = serializers.CharField(required=True)
    gender = serializers.BooleanField(default=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            "email",
            "name",
            "password",
            "phone_number",
            "organization_unit",
            "department",
            "position",
            "gender",
            "external_user_id",
            "citizen_identification",
        ]

    def validate(self, data):
        request = self.context.get("request")
        email = data.get("email", None)
        phone_number = data.get("phone_number", None)
        # validate phone number
        if User.objects.filter(phone_number=phone_number):
            raise serializers.ValidationError({"phone_number": "unique"})
        # validate email
        if User.objects.filter(email=email):
            raise serializers.ValidationError({"email": "unique"})
        try:
            validate_email(email)
        except Exception:
            raise serializers.ValidationError({"email": "invalid"})

        organization_unit_id = request.data.get("organization_unit_id", None)
        if organization_unit_id:
            if not OrganizationUnit.objects.filter(id=organization_unit_id).exists():
                raise serializers.ValidationError({"organization_unit_id": "invalid"})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        max_length=150,
        min_length=3,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length",
        },
    )
    password = serializers.CharField(
        max_length=100,
        min_length=6,
        write_only=True,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length",
        },
    )

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        user = authenticate(email=email, password=password)
        if user is None:
            raise AuthenticationFailed("Invalid email/password or Inactive Account.")
        return user
