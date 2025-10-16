"""
Vistas para la autenticación con Auth0.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import logout
from django.http import JsonResponse
from apps.usuarios.models import Usuario as User
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Endpoint de health check para autenticación"""
    return Response({
        'status': 'ok',
        'service': 'authentication',
        'message': 'Servicio de autenticación funcionando correctamente'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_auth(request):
    """Endpoint de debugging para ver información de autenticación"""
    
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    return Response({
        'status': 'debug',
        'auth_header_present': bool(auth_header),
        'auth_header_preview': auth_header[:50] + '...' if len(auth_header) > 50 else auth_header,
        'has_user': hasattr(request, 'user') and request.user.is_authenticated,
        'has_auth0_user': hasattr(request, 'auth0_user'),
        'has_auth0_claims': hasattr(request, 'auth0_claims'),
        'user_info': {
            'username': getattr(request.user, 'username', 'N/A'),
            'email': getattr(request.user, 'email', 'N/A'),
            'is_authenticated': getattr(request.user, 'is_authenticated', False)
        } if hasattr(request, 'user') else None,
        'request_path': request.path,
        'request_method': request.method
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def test_profile(request):
    """Endpoint de prueba que simula el perfil sin autenticación"""
    
    # Datos de ejemplo para probar la integración
    return Response({
        'status': 'success',
        'message': 'Endpoint de prueba funcionando',
        'profile': {
            'id': 'test-123',
            'email': 'test@example.com',
            'name': 'Usuario de Prueba',
            'role': 'Administrador',
            'status': 'Activo'
        },
        'auth_info': {
            'auth_header_present': bool(request.META.get('HTTP_AUTHORIZATION', '')),
            'is_authenticated': hasattr(request, 'user') and request.user.is_authenticated
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_auth0_profile(request):
    """Sincroniza los datos del perfil desde Auth0 usando datos del frontend"""
    try:
        user = request.user
        
        # Obtener datos del request (enviados desde el frontend)
        profile_data = request.data
        
        if not profile_data:
            return Response({
                'error': 'No se enviaron datos de perfil'
            }, status=400)
        
        # Actualizar datos desde la información enviada por el frontend
        updated_fields = []
        
        # Email
        email = profile_data.get('email')
        if email and user.email != email:
            user.email = email
            updated_fields.append('email')
        
        # Nombre completo
        name = profile_data.get('name')
        if name and user.nombre_completo != name:
            user.nombre_completo = name
            updated_fields.append('nombre_completo')
        
        # First name
        given_name = profile_data.get('given_name')
        if given_name and user.first_name != given_name:
            user.first_name = given_name
            updated_fields.append('first_name')
        
        # Last name
        family_name = profile_data.get('family_name')
        if family_name and user.last_name != family_name:
            user.last_name = family_name
            updated_fields.append('last_name')
        
        # Nickname (como backup para first_name si está vacío)
        nickname = profile_data.get('nickname')
        if nickname and not user.first_name:
            user.first_name = nickname
            updated_fields.append('first_name (from nickname)')
        
        if updated_fields:
            user.save()
            logger.info(f"✅ Usuario {user.username} actualizado: {updated_fields}")
            
        return Response({
            'status': 'success',
            'message': 'Perfil sincronizado correctamente',
            'updated_fields': updated_fields,
            'updated_profile': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nombre_completo': user.nombre_completo,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error sincronizando perfil: {str(e)}'
        }, status=500)


class UserProfileView(APIView):
    """
    Vista para obtener el perfil del usuario autenticado.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtiene el perfil del usuario autenticado"""
        try:
            user = request.user
            auth0_claims = getattr(request, 'auth0_claims', {})
            
            profile_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nombre_completo': user.nombre_completo,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'telefono': user.telefono,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'auth0_user_id': user.auth0_user_id,
                'auth0_claims': auth0_claims
            }
            
            return Response(profile_data)
            
        except Exception as e:
            return Response({
                'error': f'Error obteniendo perfil: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserManagementView(APIView):
    """
    Vista para la gestión de usuarios (solo para administradores).
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
        """
        Obtiene la lista de usuarios o un usuario específico.
        Solo para staff/superusers.
        """
        if not request.user.is_staff:
            return Response({
                'error': 'No tienes permisos para acceder a esta información'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            if user_id:
                # Obtener usuario específico
                user = User.objects.get(id=user_id)
                data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nombre_completo': user.nombre_completo,
                    'telefono': user.telefono,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'date_joined': user.date_joined,
                    'auth0_user_id': user.auth0_user_id,
                }
                return Response(data)
            else:
                # Listar usuarios
                users = User.objects.all()[:50]  # Limitar a 50 usuarios
                data = []
                for user in users:
                    data.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'nombre_completo': user.nombre_completo,
                        'is_active': user.is_active,
                        'date_joined': user.date_joined,
                    })
                
                return Response({
                    'users': data,
                    'count': len(data)
                })
                
        except User.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error obteniendo usuarios: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Vista para logout (principalmente para limpiar datos del lado del cliente).
    """
    return Response({
        'message': 'Logout exitoso. Limpia el token del cliente.'
    })
