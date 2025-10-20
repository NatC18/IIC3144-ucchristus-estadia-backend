"""
Views para el modelo Episodio
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import Episodio
from api.serializers import (
    EpisodioCreateSerializer,
    EpisodioListSerializer,
    EpisodioSerializer,
    EpisodioUpdateSerializer,
)


class EpisodioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de episodios

    Operaciones disponibles:
    - GET /api/episodios/ - Listar episodios
    - POST /api/episodios/ - Crear episodio
    - GET /api/episodios/{id}/ - Obtener episodio específico
    - PUT /api/episodios/{id}/ - Actualizar episodio completo
    - PATCH /api/episodios/{id}/ - Actualizar episodio parcial
    - DELETE /api/episodios/{id}/ - Eliminar episodio
    """

    queryset = Episodio.objects.select_related('paciente', 'cama').all()
    permission_classes = [IsAuthenticated]  # Requiere autenticación JWT

    # Filtros y búsqueda
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["paciente", "especialidad", "tipo_actividad", "inlier_outlier_flag"]
    search_fields = ["episodio_cmbd", "paciente__nombre", "paciente__rut"]
    ordering_fields = ["fecha_ingreso", "fecha_egreso", "episodio_cmbd"]
    ordering = ["-fecha_ingreso"]

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción
        """
        if self.action == "list":
            return EpisodioListSerializer
        elif self.action == "create":
            return EpisodioCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return EpisodioUpdateSerializer
        return EpisodioSerializer

    def create(self, request, *args, **kwargs):
        """
        Crear nuevo episodio
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Retornar con el serializer completo
        instance = serializer.instance
        response_serializer = EpisodioSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Endpoint personalizado para estadísticas de episodios
        GET /api/episodios/estadisticas/
        """
        total_episodios = self.get_queryset().count()
        episodios_activos = self.get_queryset().filter(fecha_egreso__isnull=True).count()
        episodios_cerrados = total_episodios - episodios_activos

        # Estadísticas por especialidad
        por_especialidad = {}
        especialidades = self.get_queryset().values_list('especialidad', flat=True).distinct()
        for especialidad in especialidades:
            if especialidad:  # Solo contar especialidades no vacías
                count = self.get_queryset().filter(especialidad=especialidad).count()
                por_especialidad[especialidad] = count

        return Response(
            {
                "total_episodios": total_episodios,
                "episodios_activos": episodios_activos,
                "episodios_cerrados": episodios_cerrados,
                "por_especialidad": por_especialidad,
            }
        )

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """
        Endpoint para obtener episodios activos (sin fecha de egreso)
        GET /api/episodios/activos/
        """
        episodios_activos = self.get_queryset().filter(fecha_egreso__isnull=True)
        
        # Aplicar filtros si existen
        filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
        for backend in filter_backends:
            episodios_activos = backend().filter_queryset(request, episodios_activos, self)

        page = self.paginate_queryset(episodios_activos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(episodios_activos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def por_paciente(self, request):
        """
        Endpoint para obtener episodios de un paciente específico
        GET /api/episodios/por_paciente/?paciente_id={id}
        """
        paciente_id = request.query_params.get('paciente_id')
        if not paciente_id:
            return Response(
                {"error": "Se requiere el parámetro paciente_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        episodios_paciente = self.get_queryset().filter(paciente_id=paciente_id)
        
        # Aplicar ordenamiento
        episodios_paciente = episodios_paciente.order_by('-fecha_ingreso')

        serializer = EpisodioSerializer(episodios_paciente, many=True)
        return Response(serializer.data)