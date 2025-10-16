"""
URLs para la aplicación de autenticación.
"""

from django.urls import path
from . import views

app_name = 'autenticacion'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health'),
    
    # Debug auth
    path('debug/', views.debug_auth, name='debug_auth'),
    path('test-profile/', views.test_profile, name='test_profile'),
    path('sync-profile/', views.sync_auth0_profile, name='sync_auth0_profile'),
    
    # Perfil de usuario
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    
    # Gestión de usuarios (solo admin)
    path('users/', views.UserManagementView.as_view(), name='user_list'),
    path('users/<int:user_id>/', views.UserManagementView.as_view(), name='user_detail'),
    
    # Logout
    path('logout/', views.logout_view, name='logout'),
]