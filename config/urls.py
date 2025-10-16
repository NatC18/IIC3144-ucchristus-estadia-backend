"""
URL configuration for UC Christus Backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.views import (
    SpectacularAPIView, 
    SpectacularSwaggerView, 
    SpectacularRedocView
)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Endpoint básico de health check"""
    return Response({
        'status': 'ok',
        'message': 'UC Christus Backend API funcionando correctamente',
        'version': '1.0.0'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def user_info(request):
    """Endpoint para mostrar info del usuario (público para pruebas)"""
    return Response({
        'status': 'success',
        'message': 'Conexión exitosa con backend',
        'authenticated': request.user.is_authenticated,
        'user_info': {
            'id': request.user.id if request.user.is_authenticated else None,
            'username': getattr(request.user, 'username', 'Anónimo'),
            'email': getattr(request.user, 'email', 'No disponible'),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_endpoint(request):
    """Endpoint protegido para probar Auth0"""
    return Response({
        'status': 'success',
        'message': 'Acceso autorizado con Auth0',
        'user_id': request.user.id,
        'user_email': getattr(request.user, 'email', 'No disponible'),
        'user_name': getattr(request.user, 'first_name', 'No disponible'),
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Health check
    path('api/health/', health_check, name='health_check'),
    
    # User info endpoint (public for testing)
    path('api/user-info/', user_info, name='user_info'),
    
    # Protected endpoint for testing Auth0
    path('api/protected/', protected_endpoint, name='protected_endpoint'),
    
    # Auth0 authentication endpoints
    path('api/auth/', include('apps.autenticacion.urls')),
    
    # Users endpoints  
    path('api/usuarios/', include('apps.usuarios.urls')),
    
    # Data loader endpoints
    path('api/data/', include('apps.data_loader.urls')),
    
    # DRF browsable API
    path('api-auth/', include('rest_framework.urls')),
]