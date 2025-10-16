"""
URLs para la aplicación API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import PacienteViewSet, login, register, logout, profile

# Router para ViewSets
router = DefaultRouter()
router.register(r'pacientes', PacienteViewSet)

urlpatterns = [
    # Rutas del router (incluye todas las operaciones CRUD)
    path('', include(router.urls)),
    
    # Autenticación personalizada
    path('auth/login/', login, name='auth_login'),
    path('auth/register/', register, name='auth_register'),
    path('auth/logout/', logout, name='auth_logout'),
    path('auth/profile/', profile, name='auth_profile'),
]