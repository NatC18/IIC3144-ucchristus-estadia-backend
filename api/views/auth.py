"""
Views para autenticación y gestión de usuarios
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Endpoint de login personalizado
    POST /api/auth/login/
    
    Body:
    {
        "username": "usuario",
        "password": "contraseña"
    }
    
    Response:
    {
        "token": "token_string",
        "user_id": 1,
        "username": "usuario"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username y password son requeridos'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
    else:
        return Response(
            {'error': 'Credenciales inválidas'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Endpoint de registro de usuarios
    POST /api/auth/register/
    
    Body:
    {
        "username": "usuario",
        "password": "contraseña",
        "email": "email@example.com",
        "first_name": "Nombre",
        "last_name": "Apellido"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    if not username or not password:
        return Response(
            {'error': 'Username y password son requeridos'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar si el usuario ya existe
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'El usuario ya existe'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar contraseña
    try:
        validate_password(password)
    except ValidationError as e:
        return Response(
            {'error': list(e.messages)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Crear usuario
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name
    )
    
    # Crear token
    token = Token.objects.create(user=user)
    
    return Response({
        'message': 'Usuario creado exitosamente',
        'token': token.key,
        'user_id': user.id,
        'username': user.username,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def logout(request):
    """
    Endpoint de logout
    POST /api/auth/logout/
    
    Headers:
    Authorization: Token <token_string>
    """
    try:
        # Eliminar el token del usuario
        request.user.auth_token.delete()
        return Response({'message': 'Logout exitoso'})
    except:
        return Response(
            {'error': 'Token inválido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def profile(request):
    """
    Endpoint para obtener información del usuario autenticado
    GET /api/auth/profile/
    
    Headers:
    Authorization: Token <token_string>
    """
    user = request.user
    return Response({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined,
        'is_staff': user.is_staff,
    })