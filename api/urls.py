"""
URLs para la aplicación API
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import EpisodioViewSet, GestionViewSet, PacienteViewSet, health_check
from api.views.archivo_views import (
    cargar_archivo,
    eliminar_archivo,
    estado_procesamiento,
    lista_archivos,
    plantilla_excel,
)
from api.views.auth import (
    CustomTokenObtainPairView,
    change_password,
    logout,
    profile,
    register,
    update_profile,
    verify_token,
)
from api.views.excel_import import import_status, upload_excel_files
from api.views.frontend_upload import (
    get_upload_status,
    list_user_uploads,
    upload_excel_frontend,
)
from api.views.process_view import ProcesarArchivoView
from api.views.upload_view import ArchivoUploadView, get_archivo_status

# Router para ViewSets
router = DefaultRouter()
router.register(r"pacientes", PacienteViewSet)
router.register(r"episodios", EpisodioViewSet)
router.register(r"gestiones", GestionViewSet)

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
    # Rutas principales para carga y procesamiento de archivos (Frontend)
    path("archivos/upload/", ArchivoUploadView.as_view(), name="archivo-upload"),
    path(
        "archivos/status/<uuid:archivo_id>/", get_archivo_status, name="archivo-status"
    ),
    path(
        "archivos/<uuid:archivo_id>/procesar/",
        ProcesarArchivoView.as_view(),
        name="archivo-procesar",
    ),
    # Rutas para archivos Excel
    path("excel/cargar/", cargar_archivo, name="cargar_archivo"),
    path(
        "excel/estado/<uuid:archivo_id>/",
        estado_procesamiento,
        name="estado_procesamiento",
    ),
    path("excel/lista/", lista_archivos, name="lista_archivos"),
    path(
        "excel/eliminar/<uuid:archivo_id>/", eliminar_archivo, name="eliminar_archivo"
    ),
    path("excel/plantilla/<str:tipo>/", plantilla_excel, name="plantilla_excel"),
    # Rutas específicas para frontend
    path("frontend/upload/", upload_excel_frontend, name="frontend_upload"),
    path(
        "frontend/upload/status/<uuid:archivo_id>/",
        get_upload_status,
        name="frontend_upload_status",
    ),
    path("frontend/upload/list/", list_user_uploads, name="frontend_upload_list"),
    # Rutas para importación de archivos Excel locales
    path("excel/import/", upload_excel_files, name="excel_import"),
    path("excel/import/status/", import_status, name="excel_import_status"),
]
