from django.contrib.auth import authenticate
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from edms.assets.models import Asset
from edms.assets.serializers import AssetSerializer
from edms.common.app_status import ErrorResponse
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

    organization_unit = serializers.SerializerMethodField()

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
            "role",
            "birthdate",
            "avatar",
            # "url",
        ]

        # extra_kwargs = {
        #     "url": {"view_name": "user-detail", "lookup_field": "pk"},
        # }

    def get_organization_unit(self, obj):
        from edms.organization.serializers import OrganizationUnitSerializer
        return OrganizationUnitSerializer(obj.organization_unit).data

    def to_representation(self, instance):
        request = self.context.get('request', None)
        data = super().to_representation(instance)
        data["role"] = "admin" if instance.is_superuser or instance.is_staff else "staff"
        data["signature_images"] = UserSignatureSerializer(
            instance.user_signature_entries.all(),
            many=True,
            context=self.context
        ).data
        if instance.organization_unit:
            data["department"] = OrganizationUnit.objects.get(id=instance.organization_unit.id).name
        return data


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        required=False,
        max_length=100,
        min_length=6,
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
            "birthdate",
            "avatar",
        ]

    def validate(self, data):
        request = self.context.get("request")
        email = data.get("email", None)
        phone_number = data.get("phone_number", None)
        # validate phone number
        if User.objects.filter(phone_number=phone_number):
            raise serializers.ValidationError({"detail": "phone_number unique"})
        # validate email
        if User.objects.filter(email=email):
            raise serializers.ValidationError({"detail": "email unique"})
        try:
            validate_email(email)
        except Exception:
            raise serializers.ValidationError({"detail": "email invalid"})

        organization_unit_id = request.data.get("organization_unit_id", None)
        if organization_unit_id:
            if not OrganizationUnit.objects.filter(id=organization_unit_id).exists():
                raise serializers.ValidationError({"detail": "organization_unit_id invalid"})
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


class UserChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        required=True,
        min_length=6,
        max_length=100,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length"
        }
    )
    new_password = serializers.CharField(
        required=True,
        min_length=6,
        max_length=100,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length"
        }
    )
    new_password_confirm = serializers.CharField(
        required=True,
        min_length=6,
        max_length=100,
        error_messages={
            "blank": "empty",
            "required": "required",
            "max_length": "max_length",
            "min_length": "min_length",
        }
    )

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError({"detail": "The current password is incorrect"})
        if data["new_password"] == data["current_password"]:
            raise serializers.ValidationError(
                {"detail": "The new password cannot be the same as the current password."}
            )
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({"detail": "The new password confirmation does not match."})
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, error_messages={
        "blank": "empty",
        "required": "required",
    }, )

    def validate(self, data):
        self.token = data["refresh"]
        return data

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError(ErrorResponse(["USER__TOKEN__EXPIRED_OR_INVALID"]).failure_response())

