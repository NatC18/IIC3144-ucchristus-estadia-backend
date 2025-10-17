"""
URLs para la aplicación API
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import PacienteViewSet, health_check
from api.views.auth import (
    CustomTokenObtainPairView,
    change_password,
    logout,
    profile,
    register,
    update_profile,
    verify_token,
)

# Router para ViewSets
router = DefaultRouter()
router.register(r"pacientes", PacienteViewSet)

urlpatterns = [
    # Rutas del router (incluye todas las operaciones CRUD)
    path("", include(router.urls)),
    # Autenticación JWT
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/register/", register, name="auth_register"),
    path("auth/logout/", logout, name="auth_logout"),
    # Gestión de perfil
    path("auth/profile/", profile, name="auth_profile"),
    path("auth/profile/update/", update_profile, name="auth_profile_update"),
    path("auth/change-password/", change_password, name="auth_change_password"),
    path("auth/verify/", verify_token, name="auth_verify_token"),
    # Health check para Render
    path("health/", health_check, name="health_check"),
]
