"""
Views para autenticación JWT y gestión de usuarios
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from ..serializers.auth import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener JWT tokens con datos del usuario
    """

    serializer_class = CustomTokenObtainPairSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    Endpoint de registro de usuarios
    POST /api/auth/register/

    Body:
    {
        "email": "usuario@example.com",
        "password": "contraseña_segura",
        "confirm_password": "contraseña_segura",
        "nombre": "Juan",
        "apellido": "Pérez",
        "rut": "12.345.678-9",
        "rol": "MEDICO"
    }

    Response:
    {
        "message": "Usuario creado exitosamente",
        "user": {...},
        "tokens": {
            "access": "...",
            "refresh": "..."
        }
    }
    """
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        # Generar tokens JWT para el usuario recién creado
        refresh = RefreshToken.for_user(user)
        tokens = {"access": str(refresh.access_token), "refresh": str(refresh)}

        # Serializar datos del usuario
        user_serializer = UserProfileSerializer(user)

        return Response(
            {
                "message": "Usuario creado exitosamente",
                "user": user_serializer.data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Endpoint de logout (blacklist del refresh token)
    POST /api/auth/logout/

    Headers:
    Authorization: Bearer <access_token>

    Body:
    {
        "refresh": "refresh_token_here"
    }
    """
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        return Response({"message": "Logout exitoso"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "Token inválido o error al hacer logout"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Endpoint para obtener información del usuario autenticado
    GET /api/auth/profile/

    Headers:
    Authorization: Bearer <access_token>

    Response:
    {
        "id": "uuid",
        "email": "usuario@example.com",
        "nombre": "Juan",
        "apellido": "Pérez",
        "nombre_completo": "Juan Pérez",
        "rut": "12.345.678-9",
        "rol": "MEDICO",
        "is_staff": false,
        "date_joined": "2024-01-01T00:00:00Z",
        "last_login": "2024-01-01T00:00:00Z"
    }
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Endpoint para actualizar información del usuario autenticado
    PUT/PATCH /api/auth/profile/update/

    Headers:
    Authorization: Bearer <access_token>

    Body (campos opcionales):
    {
        "nombre": "Nuevo Nombre",
        "apellido": "Nuevo Apellido",
        "rol": "ENFERMERO"
    }
    """
    serializer = UserProfileSerializer(
        request.user, data=request.data, partial=request.method == "PATCH"
    )

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Perfil actualizado exitosamente", "user": serializer.data},
            status=status.HTTP_200_OK,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Endpoint para cambiar contraseña
    POST /api/auth/change-password/

    Headers:
    Authorization: Bearer <access_token>

    Body:
    {
        "old_password": "contraseña_actual",
        "new_password": "nueva_contraseña",
        "confirm_password": "nueva_contraseña"
    }
    """
    serializer = ChangePasswordSerializer(
        data=request.data, context={"user": request.user}
    )

    if serializer.is_valid():
        # Cambiar la contraseña
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()

        return Response(
            {"message": "Contraseña cambiada exitosamente"}, status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """
    Endpoint para verificar si un token JWT es válido
    GET /api/auth/verify/

    Headers:
    Authorization: Bearer <access_token>

    Response:
    {
        "valid": true,
        "user": {...}
    }
    """
    serializer = UserProfileSerializer(request.user)
    return Response({"valid": True, "user": serializer.data}, status=status.HTTP_200_OK)
