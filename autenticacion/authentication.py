"""
Clases de autenticación personalizadas para Django REST Framework con Auth0.
"""

from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model
from .middleware import Auth0Middleware

User = get_user_model()


class Auth0Authentication(authentication.BaseAuthentication):
    """
    Clase de autenticación personalizada para Auth0 JWT tokens en DRF.
    """
    
    def authenticate(self, request):
        """
        Autentica la petición y retorna una tupla de (user, token).
        """
        
        # Evitar recursión - si ya estamos procesando auth, retornar None
        if hasattr(request, '_auth_processing'):
            return None
        
        # SOLUCIÓN CORRECTA: No acceder a request.user aquí
        # Verificar si el middleware ya procesó la autenticación
        if hasattr(request, 'auth0_user') and hasattr(request, 'auth0_claims'):
            return (request.auth0_user, request.auth0_claims)
        
        # Si no hay header de autorización, no intentar autenticar
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        # Marcar que estamos procesando para evitar recursión
        request._auth_processing = True
        
        try:
            token = auth_header.split(' ')[1]
            
            # Usar la misma lógica de validación que el middleware
            middleware = Auth0Middleware()
            
            user_info = middleware._validate_jwt_token(token)
            if not user_info:
                raise exceptions.AuthenticationFailed('Token inválido')
            
            user = middleware._get_or_create_user(user_info)
            if not user:
                raise exceptions.AuthenticationFailed('Usuario no encontrado o inactivo')
            
            return (user, user_info)
            
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Error de autenticación: {str(e)}')
        finally:
            # Limpiar flag de procesamiento
            if hasattr(request, '_auth_processing'):
                delattr(request, '_auth_processing')
    
    def authenticate_header(self, request):
        """
        Retorna el header de autenticación usado por la API.
        """
        return 'Bearer'