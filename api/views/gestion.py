"""
Views para el modelo Gestion
"""

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import Gestion
from api.serializers import GestionSerializer


class GestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de gestiones

    Operaciones disponibles:
    - GET /api/gestiones/ - Listar gestiones
    - POST /api/gestiones/ - Crear gestión
    - GET /api/gestiones/{id}/ - Obtener gestión específica
    - PUT /api/gestiones/{id}/ - Actualizar gestión completa
    - PATCH /api/gestiones/{id}/ - Actualizar gestión parcial
    - DELETE /api/gestiones/{id}/ - Eliminar gestión
    """

    queryset = Gestion.objects.select_related("episodio", "usuario").all()
    serializer_class = GestionSerializer
    permission_classes = [IsAuthenticated]

    # Filtros y búsqueda
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado_gestion", "tipo_gestion", "episodio", "usuario"]
    search_fields = ["tipo_gestion", "informe"]
    ordering_fields = ["fecha_inicio", "fecha_fin", "created_at"]
    ordering = ["-fecha_inicio"]

    @action(detail=False, methods=["get"])
    def pendientes(self, request):
        """
        Listar gestiones pendientes (INICIADA o EN_PROGRESO)
        GET /api/gestiones/pendientes/
        """
        gestiones_pendientes = self.get_queryset().filter(
            estado_gestion__in=["INICIADA", "EN_PROGRESO"]
        )
        serializer = self.get_serializer(gestiones_pendientes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Estadísticas de gestiones para el dashboard
        GET /api/gestiones/estadisticas/
        """
        queryset = self.get_queryset()

        # Contar por estado
        por_estado = (
            queryset.values("estado_gestion")
            .annotate(cantidad=Count("id"))
            .order_by("estado_gestion")
        )

        # Contar por tipo de gestión
        por_tipo = (
            queryset.values("tipo_gestion")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")
        )

        # Transformar tipo_gestion a nombres legibles
        tipo_gestion_data = []
        for item in por_tipo:
            # Obtener el display name usando el modelo
            tipo_code = item["tipo_gestion"]
            # Buscar el label del choice
            tipo_label = dict(Gestion.TIPO_GESTION_CHOICES).get(tipo_code, tipo_code)
            tipo_gestion_data.append({
                "tipo_gestion": tipo_label,
                "cantidad": item["cantidad"]
            })

        return Response(
            {
                "total_gestiones": queryset.count(),
                "por_estado": list(por_estado),
                "por_tipo": list(por_tipo),
                "por_tipo_gestion": tipo_gestion_data,
            }
        )

    @action(detail=False, methods=["get"])
    def tareas_pendientes(self, request):
        """
        Lista de tareas pendientes formateadas para el dashboard
        GET /api/gestiones/tareas_pendientes/
        """
        gestiones = (
            self.get_queryset()
            .filter(estado_gestion__in=["INICIADA", "EN_PROGRESO"])
            .select_related("episodio", "episodio__paciente")[:10]
        )

        # Mapeo de estados
        estado_map = {
            "INICIADA": "Abierta",
            "EN_PROGRESO": "En proceso",
            "COMPLETADA": "Cerrada",
            "CANCELADA": "Cancelada",
        }

        data = []
        for g in gestiones:
            data.append(
                {
                    "id": str(g.id),
                    "episodio": str(g.episodio.episodio_cmbd),
                    "tipo_gestion": g.get_tipo_gestion_display(),
                    "descripcion": g.informe
                    or f"Gestión de {g.get_tipo_gestion_display()}",
                    "estado": estado_map.get(g.estado_gestion, "Abierta"),
                    "fecha_inicio": g.fecha_inicio.isoformat() if g.fecha_inicio else None,
                }
            )

        return Response(data)
