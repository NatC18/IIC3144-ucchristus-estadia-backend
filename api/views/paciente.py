"""
Views para el modelo Paciente
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.models import Paciente
from api.serializers import (
    PacienteCreateSerializer,
    PacienteListSerializer,
    PacienteSerializer,
)


class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de pacientes

    Operaciones disponibles:
    - GET /api/pacientes/ - Listar pacientes
    - POST /api/pacientes/ - Crear paciente
    - GET /api/pacientes/{id}/ - Obtener paciente específico
    - PUT /api/pacientes/{id}/ - Actualizar paciente completo
    - PATCH /api/pacientes/{id}/ - Actualizar paciente parcial
    - DELETE /api/pacientes/{id}/ - Eliminar paciente
    """

    queryset = Paciente.objects.all()
    permission_classes = [IsAuthenticated]  # Requiere autenticación JWT

    # Filtros y búsqueda
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["sexo", "prevision_1", "prevision_2"]
    search_fields = ["nombre", "rut"]
    ordering_fields = ["nombre", "fecha_nacimiento", "created_at"]
    ordering = ["nombre"]

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción
        """
        if self.action == "list":
            return PacienteListSerializer
        elif self.action == "create":
            return PacienteCreateSerializer
        return PacienteSerializer

    def create(self, request, *args, **kwargs):
        """
        Crear nuevo paciente
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Retornar con el serializer completo
        instance = serializer.instance
        response_serializer = PacienteSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Endpoint personalizado para estadísticas de pacientes
        GET /api/pacientes/estadisticas/
        """
        total_pacientes = self.get_queryset().count()
        por_sexo = {}
        por_prevision = {}

        for choice_value, choice_label in Paciente.SEXO_CHOICES:
            count = self.get_queryset().filter(sexo=choice_value).count()
            por_sexo[choice_label] = count

        for choice_value, choice_label in Paciente.PREVISION_CHOICES:
            count = self.get_queryset().filter(prevision=choice_value).count()
            por_prevision[choice_label] = count

        return Response(
            {
                "total_pacientes": total_pacientes,
                "por_sexo": por_sexo,
                "por_prevision": por_prevision,
            }
        )

    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        """
        Endpoint para historial de un paciente específico
        GET /api/pacientes/{id}/historial/
        """
        paciente = self.get_object()
        # Aquí podrías agregar lógica para obtener historial médico
        return Response(
            {
                "paciente_id": paciente.id,
                "paciente_nombre": paciente.nombre,
                "historial": [],  # Placeholder para futuras implementaciones
                "message": "Historial no implementado aún",
            }
        )
