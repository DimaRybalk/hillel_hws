from rest_framework import serializers
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "username",
            "is_staff",
            "is_active",
            "role",
            "role_display",
        ]
        read_only_fields = ["id", "is_staff", "is_active", "role_display"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = CustomUser
        fields = ["id", "email", "username", "password", "role"]

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)
