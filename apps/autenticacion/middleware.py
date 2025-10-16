"""
Middleware para la autenticación con Auth0 usando JWT tokens.
"""

import json
import jwt
import requests
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.core.cache import cache
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
import base64

User = get_user_model()
logger = logging.getLogger(__name__)


class Auth0Middleware:
    """
    Middleware para validar tokens JWT de Auth0 y autenticar usuarios.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process the request
        response = self.process_request(request)
        if response:
            return response
        
        # Get response from next middleware/view
        response = self.get_response(request)
        return response
    
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
        '/api/auth/debug/',  # Debug endpoint
    ]
    
    def process_request(self, request):
        """
        Procesa la petición para validar el token JWT de Auth0.
        """
        
        # Debug: log de todas las peticiones a endpoints de auth
        if request.path.startswith('/api/auth/'):
            logger.debug(f"🚀 Request a {request.path} desde {request.META.get('HTTP_ORIGIN', 'unknown')}")
            logger.debug(f"🔑 Headers Authorization: {request.META.get('HTTP_AUTHORIZATION', 'No token')}")
        
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
        logger.debug(f"🎫 Token recibido: {token[:50]}... (longitud: {len(token)})")
        
        # Verificar formato básico del JWT
        token_parts = token.split('.')
        logger.debug(f"🔍 Partes del token: {len(token_parts)} (debe ser 3)")
        
        try:
            # Validar y decodificar el token JWT
            logger.debug("🔐 Iniciando validación JWT...")
            user_info = self._validate_jwt_token(token)
            logger.debug(f"👤 User info obtenida: {user_info}")
            if not user_info:
                logger.debug("❌ No se pudo obtener user_info del token")
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
            logger.debug("🔑 Obteniendo clave pública de Auth0...")
            # Obtener la clave pública de Auth0 (con cache)
            jwks = self._get_auth0_public_key()
            if not jwks:
                logger.debug("❌ No se pudo obtener JWKS de Auth0")
                raise jwt.InvalidTokenError("No se pudo obtener la clave pública de Auth0")
            logger.debug("✅ JWKS obtenido correctamente")
            
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
            
            # Convertir JWK a formato PEM
            pem_key = self._jwk_to_pem(rsa_key)
            
            # Validar configuración crítica de seguridad
            audience = getattr(settings, 'AUTH0_AUDIENCE', None)
            domain = getattr(settings, 'AUTH0_DOMAIN', None)
            
            if not audience:
                raise jwt.InvalidTokenError("AUTH0_AUDIENCE no configurado - validación de audiencia requerida")
            
            if not domain:
                raise jwt.InvalidTokenError("AUTH0_DOMAIN no configurado - validación de issuer requerida")
            
            issuer = f"https://{domain}/"
            
            # Decodificar y validar el token
            logger.debug(f"🔍 Validando token con audience: {audience}")
            logger.debug(f"🔍 Validando token con issuer: {issuer}")
            payload = jwt.decode(
                token,
                pem_key,
                algorithms=["RS256"],
                audience=audience,
                issuer=issuer
            )
            
            logger.debug(f"✅ Token validado correctamente. Payload: {payload}")
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
    
    def _get_auth0_user_profile(self, auth0_user_id):
        """
        Obtiene información del perfil del usuario desde Auth0 userinfo endpoint.
        """
        try:
            from django.conf import settings
            auth0_domain = getattr(settings, 'AUTH0_DOMAIN', '')
            
            if not auth0_domain:
                logger.error("AUTH0_DOMAIN no configurado")
                return None
            
            # Para obtener el perfil del usuario, necesitamos hacer una request con Management API
            # Por simplicidad, vamos a usar el endpoint userinfo con el token actual
            # Pero esto requiere que el token tenga el scope correcto
            
            # Por ahora, vamos a intentar obtener info básica desde el 'sub' 
            # Extraer información básica del sub
            provider_info = auth0_user_id.split('|')
            if len(provider_info) >= 2:
                provider = provider_info[0]
                provider_user_id = provider_info[1]
                
                # Si es Google OAuth, podemos inferir algunas cosas
                if provider == 'google-oauth2':
                    return {
                        'provider': 'Google',
                        'provider_user_id': provider_user_id
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo perfil de Auth0: {str(e)}")
            return None
    
    def _get_or_create_user(self, user_info):
        """
        Obtiene o crea un usuario basado en la información de Auth0.
        """
        try:
            auth0_user_id = user_info.get('sub')
            email = user_info.get('email')
            
            # El JWT básico no contiene información del perfil, necesitamos obtenerla del userinfo endpoint
            logger.info(f"🔍 JWT claims: {user_info}")
            
            # Obtener información del perfil desde Auth0 userinfo endpoint
            profile_info = self._get_auth0_user_profile(auth0_user_id)
            if profile_info:
                # Combinar JWT claims con información del perfil
                user_info.update(profile_info)
                logger.info(f"👤 Perfil completo obtenido: {profile_info}")
            
            email = user_info.get('email')
            logger.info(f"� Email final: {email}")
            logger.info(f"👤 Nombre final: {user_info.get('name')}")
            
            if not auth0_user_id:
                logger.error("No se encontró 'sub' en la información del usuario de Auth0")
                return None
            
            # Buscar usuario por auth0_user_id
            try:
                user = User.objects.get(auth0_user_id=auth0_user_id)
                
                # Actualizar información si es necesario
                updated = False
                
                # Email
                if email and user.email != email:
                    user.email = email
                    updated = True
                
                # Nombre completo
                if user_info.get('name') and user.nombre_completo != user_info.get('name'):
                    user.nombre_completo = user_info.get('name')
                    updated = True
                
                # First name
                given_name = user_info.get('given_name')
                if given_name and user.first_name != given_name:
                    user.first_name = given_name
                    updated = True
                
                # Last name
                family_name = user_info.get('family_name')
                if family_name and user.last_name != family_name:
                    user.last_name = family_name
                    updated = True
                
                # Si no tiene nombre/apellido pero tiene nickname, usarlo
                nickname = user_info.get('nickname')
                if nickname and not user.first_name and not user.last_name:
                    user.first_name = nickname
                    updated = True
                
                if updated:
                    user.save()
                    logger.info(f"Usuario actualizado desde Auth0: {user.username}")
                
                return user
                
            except User.DoesNotExist:
                # Extraer información de Auth0
                email = user_info.get('email', '')
                name = user_info.get('name', '')
                given_name = user_info.get('given_name', '')
                family_name = user_info.get('family_name', '')
                nickname = user_info.get('nickname', '')
                
                # Generar username desde email o usar fallback
                if email:
                    username_base = email.split('@')[0]
                else:
                    username_base = nickname or f"user_{auth0_user_id[-8:]}"
                
                # Asegurar username único
                username = username_base
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{username_base}_{counter}"
                    counter += 1
                
                # Si no hay given_name/family_name pero hay name completo, intentar separarlo
                if not given_name and not family_name and name:
                    name_parts = name.strip().split(' ', 1)
                    given_name = name_parts[0] if len(name_parts) > 0 else ''
                    family_name = name_parts[1] if len(name_parts) > 1 else ''
                
                # Si aún no hay nombres, usar nickname
                if not given_name and nickname:
                    given_name = nickname
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    auth0_user_id=auth0_user_id,
                    nombre_completo=name,
                    first_name=given_name,
                    last_name=family_name,
                )
                
                logger.info(f"✅ Usuario creado desde Auth0: {user.username}")
                logger.info(f"📧 Email: {user.email}")
                logger.info(f"👤 Nombre completo: {user.nombre_completo}")
                logger.info(f"👤 First name: {user.first_name}")
                logger.info(f"👤 Last name: {user.last_name}")
                
                return user
                
        except Exception as e:
            logger.error(f"Error creando/obteniendo usuario: {str(e)}")
            return None
    
    def _jwk_to_pem(self, jwk):
        """
        Convierte una clave JWK a formato PEM para PyJWT.
        """
        try:
            # Decodificar los componentes de la clave RSA desde base64url
            def base64url_decode(input_str):
                # Agregar padding si es necesario
                padding = 4 - len(input_str) % 4
                if padding != 4:
                    input_str += '=' * padding
                return base64.urlsafe_b64decode(input_str)
            
            # Obtener n y e del JWK
            n = int.from_bytes(base64url_decode(jwk['n']), byteorder='big')
            e = int.from_bytes(base64url_decode(jwk['e']), byteorder='big')
            
            # Crear el objeto RSAPublicNumbers
            public_numbers = RSAPublicNumbers(e=e, n=n)
            public_key = public_numbers.public_key()
            
            # Serializar a formato PEM
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return pem
            
        except Exception as e:
            logger.error(f"Error convirtiendo JWK a PEM: {str(e)}")
            raise jwt.InvalidTokenError(f"Error procesando clave pública: {str(e)}")