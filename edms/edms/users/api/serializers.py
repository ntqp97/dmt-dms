from django.contrib.auth import authenticate
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from edms.organization.models import OrganizationUnit
from edms.users.models import User


class UserSerializer(serializers.ModelSerializer[User]):
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
            # "url",
        ]

        # extra_kwargs = {
        #     "url": {"view_name": "user-detail", "lookup_field": "pk"},
        # }

    def to_representation(self, instance):
        return super().to_representation(instance)


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
    phone_number = serializers.CharField(
        required=True,
        max_length=15,
        min_length=6,
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
