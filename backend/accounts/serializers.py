"""Serializers for registration and login."""

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Validate and create new Quizly users."""

    confirmed_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        """Fields accepted by the registration endpoint."""

        model = User
        fields = ("username", "email", "password", "confirmed_password")

    def validate(self, attrs):
        """Validate matching passwords and unique email addresses."""
        validate_password_match(attrs)
        validate_unique_email(attrs["email"])
        return attrs

    def create(self, validated_data):
        """Create a user with a securely hashed password."""
        validated_data.pop("confirmed_password")
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Validate login credentials without leaking account state."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate a user or raise a generic error."""
        user = authenticate(**attrs)
        if user is None:
            raise serializers.ValidationError({"detail": "Invalid credentials."})
        attrs["user"] = user
        return attrs


def validate_password_match(attrs):
    """Ensure the repeated password matches the password."""
    if attrs["password"] != attrs["confirmed_password"]:
        raise serializers.ValidationError(
            {"confirmed_password": "Passwords do not match."}
        )


def validate_unique_email(email):
    """Reject duplicate email addresses case-insensitively."""
    if User.objects.filter(email__iexact=email).exists():
        raise serializers.ValidationError({"email": "Email already exists."})
