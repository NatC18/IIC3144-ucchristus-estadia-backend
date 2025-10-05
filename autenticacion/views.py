"""
Vistas para la autenticación con Auth0.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from usuarios.models import Usuario

User = get_user_model()


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Endpoint de health check para autenticación"""
    return Response({
        'status': 'ok',
        'service': 'authentication',
        'message': 'Servicio de autenticación funcionando correctamente'
    })


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
                user = Usuario.objects.get(id=user_id)
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
                users = Usuario.objects.all()[:50]  # Limitar a 50 usuarios
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
                
        except Usuario.DoesNotExist:
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
