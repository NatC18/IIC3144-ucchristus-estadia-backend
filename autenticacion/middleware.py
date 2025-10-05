"""
Middleware para la autenticación con Auth0 usando JWT tokens.
"""

import json
import jwt
import requests
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Auth0Middleware(MiddlewareMixin):
    """
    Middleware para validar tokens JWT de Auth0 y autenticar usuarios.
    """
    
    # Rutas que no requieren autenticación
    EXEMPT_PATHS = [
        '/admin/',
        '/api/health/',
        '/api/docs/',
        '/api/redoc/',
        '/api/schema/',
        '/api-auth/',
        '/static/',
        '/favicon.ico',
        '/api/auth/health/',  # Health check específico
    ]
    
    def process_request(self, request):
        """
        Procesa la petición para validar el token JWT de Auth0.
        """
        
        # Skip autenticación para rutas exentas
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return None
        
        # Skip para peticiones OPTIONS (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        # Skip si estamos ejecutando comandos de Django
        import sys
        if any(arg in sys.argv for arg in ['shell', 'migrate', 'makemigrations', 'createsuperuser', 'runserver']):
            return None
        
        # Skip si ya procesamos esta request (evitar recursión)
        if hasattr(request, '_auth0_processed'):
            return None
        request._auth0_processed = True
        
        # Extraer token del header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            # En desarrollo, permitir acceso sin token para ciertos endpoints
            from django.conf import settings
            if settings.DEBUG:
                # Solo requerir autenticación para endpoints específicos en desarrollo
                auth_required_paths = [
                    '/api/auth/profile/',
                    '/api/auth/users/',
                ]
                if any(request.path.startswith(path) for path in auth_required_paths):
                    return JsonResponse({
                        'error': 'Token de autorización requerido'
                    }, status=401)
                return None
            else:
                # En producción, requerir token para todas las APIs
                exempt_paths = any(request.path.startswith(path) for path in self.EXEMPT_PATHS)
                if request.path.startswith('/api/') and not exempt_paths:
                    return JsonResponse({
                        'error': 'Token de autorización requerido'
                    }, status=401)
                return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Validar y decodificar el token JWT
            user_info = self._validate_jwt_token(token)
            if not user_info:
                return JsonResponse({
                    'error': 'Token inválido o expirado'
                }, status=401)
            
            # Obtener o crear el usuario basado en la información de Auth0
            user = self._get_or_create_user(user_info)
            if not user:
                return JsonResponse({
                    'error': 'Usuario no encontrado o inactivo'
                }, status=401)
            
            # Adjuntar usuario y claims a la request
            # Usar nombres específicos para evitar conflictos con DRF
            request.auth0_user = user
            request.auth0_claims = user_info
            # También setear request.user para compatibilidad con Django
            request.user = user
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({
                'error': 'Token expirado'
            }, status=401)
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token JWT inválido: {str(e)}")
            return JsonResponse({
                'error': 'Token inválido'
            }, status=401)
        except Exception as e:
            logger.error(f"Error en autenticación Auth0: {str(e)}")
            return JsonResponse({
                'error': 'Error de autenticación'
            }, status=500)
        
        return None
    
    def _validate_jwt_token(self, token):
        """
        Valida el token JWT contra Auth0.
        """
        try:
            # Obtener la clave pública de Auth0 (con cache)
            jwks = self._get_auth0_public_key()
            if not jwks:
                raise jwt.InvalidTokenError("No se pudo obtener la clave pública de Auth0")
            
            # Obtener el key ID del header del token
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            
            # Buscar la clave correcta
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
            
            if not rsa_key:
                raise jwt.InvalidTokenError("Clave pública no encontrada")
            
            # Decodificar y validar el token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=getattr(settings, 'AUTH0_AUDIENCE', None),
                issuer=f"https://{getattr(settings, 'AUTH0_DOMAIN', '')}/"
            )
            
            return payload
            
        except Exception as e:
            logger.error(f"Error validando token JWT: {str(e)}")
            return None
    
    def _get_auth0_public_key(self):
        """
        Obtiene las claves públicas de Auth0 con cache.
        """
        cache_key = 'auth0_jwks'
        jwks = cache.get(cache_key)
        
        if not jwks:
            try:
                auth0_domain = getattr(settings, 'AUTH0_DOMAIN', '')
                if not auth0_domain:
                    logger.error("AUTH0_DOMAIN no configurado en settings")
                    return None
                
                response = requests.get(f"https://{auth0_domain}/.well-known/jwks.json", timeout=10)
                response.raise_for_status()
                jwks = response.json()
                
                # Cache por 1 hora
                cache.set(cache_key, jwks, 3600)
                
            except Exception as e:
                logger.error(f"Error obteniendo claves públicas de Auth0: {str(e)}")
                return None
        
        return jwks
    
    def _get_or_create_user(self, user_info):
        """
        Obtiene o crea un usuario basado en la información de Auth0.
        """
        try:
            auth0_user_id = user_info.get('sub')
            email = user_info.get('email')
            
            if not auth0_user_id:
                logger.error("No se encontró 'sub' en la información del usuario de Auth0")
                return None
            
            # Buscar usuario por auth0_user_id
            try:
                user = User.objects.get(auth0_user_id=auth0_user_id)
                
                # Actualizar información si es necesario
                updated = False
                if email and user.email != email:
                    user.email = email
                    updated = True
                
                if user_info.get('name') and user.nombre_completo != user_info.get('name'):
                    user.nombre_completo = user_info.get('name')
                    updated = True
                
                if updated:
                    user.save()
                
                return user
                
            except User.DoesNotExist:
                # Crear nuevo usuario
                username = email.split('@')[0] if email else f"user_{auth0_user_id[-8:]}"
                
                # Asegurar username único
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email or '',
                    auth0_user_id=auth0_user_id,
                    nombre_completo=user_info.get('name', ''),
                    first_name=user_info.get('given_name', ''),
                    last_name=user_info.get('family_name', ''),
                )
                
                logger.info(f"Usuario creado desde Auth0: {user.username}")
                return user
                
        except Exception as e:
            logger.error(f"Error creando/obteniendo usuario: {str(e)}")
            return None