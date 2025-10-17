"""
Serializers para autenticación JWT
"""

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para JWT que incluye datos del usuario en la respuesta
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar datos personalizados al token
        token["nombre"] = user.nombre
        token["apellido"] = user.apellido
        token["email"] = user.email
        token["rol"] = user.rol

        return token

    def validate(self, attrs):
        # Validar usando email como username
        data = super().validate(attrs)

        # Agregar información del usuario a la respuesta
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "nombre": self.user.nombre,
            "apellido": self.user.apellido,
            "nombre_completo": self.user.nombre_completo,
            "rol": self.user.rol,
            "is_staff": self.user.is_staff,
        }

        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de nuevos usuarios
    """

    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "confirm_password",
            "nombre",
            "apellido",
            "rut",
            "rol",
        )
        extra_kwargs = {
            "email": {"required": True},
            "nombre": {"required": True},
            "apellido": {"required": True},
            "rut": {"required": True},
        }

    def validate_email(self, value):
        """Validar que el email sea único"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email.")
        return value

    def validate_rut(self, value):
        """Validar formato de RUT"""
        if not re.match(r"^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$", value):
            raise serializers.ValidationError(
                "Formato de RUT inválido. Use: XX.XXX.XXX-X"
            )

        if User.objects.filter(rut=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este RUT.")
        return value

    def validate_password(self, value):
        """Validar contraseña usando los validadores de Django"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Validaciones adicionales"""
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas no coinciden."}
            )

        # Remover confirm_password de los datos validados
        attrs.pop("confirm_password", None)
        return attrs

    def create(self, validated_data):
        """Crear nuevo usuario"""
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil del usuario (lectura y actualización)
    """

    nombre_completo = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nombre",
            "apellido",
            "nombre_completo",
            "rut",
            "rol",
            "is_staff",
            "date_joined",
            "last_login",
        )
        read_only_fields = (
            "id",
            "email",
            "rut",
            "date_joined",
            "last_login",
            "is_staff",
        )

    def validate_nombre(self, value):
        """Validar que el nombre no esté vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre es requerido.")
        return value.strip()

    def validate_apellido(self, value):
        """Validar que el apellido no esté vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError("El apellido es requerido.")
        return value.strip()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambio de contraseña
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        """Validar la contraseña actual"""
        user = self.context["user"]
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value

    def validate_new_password(self, value):
        """Validar nueva contraseña"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas no coinciden."}
            )

        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar usuarios (solo campos básicos)
    """

    nombre_completo = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nombre",
            "apellido",
            "nombre_completo",
            "rol",
            "is_active",
        )
