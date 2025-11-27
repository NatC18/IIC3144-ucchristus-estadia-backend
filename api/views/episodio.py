"""
Views para el modelo Episodio
"""

from django.db.models import Avg, Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import Episodio, EpisodioServicio
from api.serializers import (
    EpisodioCreateSerializer,
    EpisodioSerializer,
    EpisodioServicioSerializer,
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

    queryset = Episodio.objects.select_related("paciente", "cama").all()
    permission_classes = [IsAuthenticated]

    # Filtros y búsqueda
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["paciente", "tipo_actividad", "especialidad"]
    search_fields = ["episodio_cmbd", "paciente__nombre"]
    ordering_fields = ["fecha_ingreso", "fecha_egreso", "created_at"]
    ordering = ["-fecha_ingreso"]

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == "create":
            return EpisodioCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return EpisodioUpdateSerializer
        return EpisodioSerializer

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """
        Listar episodios activos (sin fecha de egreso)
        GET /api/episodios/activos/
        """
        episodios_activos = self.get_queryset().filter(fecha_egreso__isnull=True)
        serializer = self.get_serializer(episodios_activos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Endpoint para estadísticas generales de episodios
        GET /api/episodios/estadisticas/
        """
        queryset = self.get_queryset()
        episodios_activos = queryset.filter(fecha_egreso__isnull=True)
        episodios_egresados = queryset.filter(fecha_egreso__isnull=False)

        # Calcular promedio de estadía (TODOS los episodios)
        total_dias = 0
        count = 0
        hoy = timezone.now().date()

        # Episodios cerrados: usar fecha de egreso
        for ep in episodios_egresados:
            if ep.fecha_egreso and ep.fecha_ingreso:
                dias = (ep.fecha_egreso.date() - ep.fecha_ingreso.date()).days
                total_dias += dias
                count += 1

        # Episodios activos: usar fecha actual (hasta hoy)
        for ep in episodios_activos:
            if ep.fecha_ingreso:
                dias = (hoy - ep.fecha_ingreso.date()).days
                total_dias += dias
                count += 1

        promedio_estadia = round(total_dias / count, 1) if count > 0 else 0

        # Contar extensiones críticas (calculado dinámicamente)
        extensiones_criticas = 0
        for ep in episodios_activos:
            dias_estadia = (hoy - ep.fecha_ingreso.date()).days
            if ep.estancia_norma_grd and dias_estadia > ep.estancia_norma_grd * (4 / 3):
                extensiones_criticas += 1

        # Altas de hoy
        altas_hoy = episodios_egresados.filter(fecha_egreso__date=hoy).count()

        return Response(
            {
                "total_episodios": queryset.count(),
                "episodios_activos": episodios_activos.count(),
                "episodios_egresados": episodios_egresados.count(),
                "promedio_estadia_dias": promedio_estadia,
                "extensiones_criticas": extensiones_criticas,
                "altas_hoy": altas_hoy,
            }
        )

    @action(detail=False, methods=["get"])
    def extensiones_criticas(self, request):
        """
        Listar episodios con extensión crítica (outliers activos)
        GET /api/episodios/extensiones_criticas/
        """
        episodios = (
            self.get_queryset()
            .filter(fecha_egreso__isnull=True)
            .select_related("paciente")
        )

        data = []
        hoy = timezone.now().date()
        for ep in episodios:
            dias_estadia = (hoy - ep.fecha_ingreso.date()).days
            if ep.estancia_norma_grd:
                if dias_estadia > ep.estancia_norma_grd * (4 / 3):
                    data.append(
                        {
                            "id": ep.id,
                            "episodio": str(ep.episodio_cmbd),
                            "paciente": ep.paciente.nombre,
                            "dias_estadia": dias_estadia,
                            "fecha_ingreso": ep.fecha_ingreso,
                            "dias_esperados": ep.estancia_norma_grd,
                        }
                    )
            # Si no hay norma, puedes decidir si mostrar o no

        return Response(data)

    @action(detail=False, methods=["get"])
    def tendencia_estadia(self, request):
        """
        Obtener tendencia de pacientes por mes (últimos 12 meses)
        GET /api/episodios/tendencia_estadia/
        """
        from collections import defaultdict
        from datetime import timedelta

        hoy = timezone.now().date()
        hace_12_meses = hoy - timedelta(days=365)

        # Obtener episodios de los últimos 12 meses
        episodios = self.get_queryset().filter(fecha_ingreso__gte=hace_12_meses)

        # Agrupar por mes
        meses_data = defaultdict(set)  # usar set para contar pacientes únicos

        for ep in episodios:
            mes_anio = ep.fecha_ingreso.strftime("%Y-%m")
            meses_data[mes_anio].add(ep.paciente_id)

        # Preparar los últimos 12 meses en orden
        resultado = []
        meses_nombres = [
            "Ene",
            "Feb",
            "Mar",
            "Abr",
            "May",
            "Jun",
            "Jul",
            "Ago",
            "Sep",
            "Oct",
            "Nov",
            "Dic",
        ]

        for i in range(11, -1, -1):
            fecha_mes = hoy - timedelta(days=30 * i)
            mes_key = fecha_mes.strftime("%Y-%m")
            mes_nombre = meses_nombres[int(fecha_mes.strftime("%m")) - 1]

            resultado.append(
                {"mes": mes_nombre, "pacientes": len(meses_data.get(mes_key, set()))}
            )

        return Response(resultado)

    @action(detail=False, methods=["get"])
    def alertas_prediccion(self, request):
        """
        Listar episodios activos con predicción de estadía larga
        GET /api/episodios/alertas_prediccion/

        Retorna episodios activos que:
        - Tienen prediccion_extension = 1 (modelo ML predice extensión)
        - NO están ya en extensión crítica (no se han pasado)
        """
        episodios = (
            self.get_queryset()
            .filter(fecha_egreso__isnull=True, prediccion_extension=1)
            .select_related("paciente")
        )

        data = []
        hoy = timezone.now().date()

        for ep in episodios:
            dias_estadia = (hoy - ep.fecha_ingreso.date()).days

            # Verificar que NO esté en extensión crítica
            tiene_extension_critica = False
            if ep.estancia_norma_grd and dias_estadia > ep.estancia_norma_grd * (4 / 3):
                tiene_extension_critica = True

            # Solo incluir si NO tiene extensión crítica (aún no se ha pasado)
            if not tiene_extension_critica:
                data.append(
                    {
                        "id": ep.id,
                        "episodio": str(ep.episodio_cmbd),
                        "paciente": ep.paciente.nombre,
                        "dias_estadia": dias_estadia,
                        "dias_esperados": ep.estancia_norma_grd,
                        "fecha_ingreso": ep.fecha_ingreso,
                    }
                )

        return Response(data)

    @action(detail=True, methods=["get"], url_path="servicios")
    def servicios(self, request, pk=None):
        """
        Devuelve todos los servicios asociados al episodio.
        """
        relaciones = (
            EpisodioServicio.objects.filter(episodio_id=pk)
            .select_related("servicio")
            .order_by("tipo")
        )

        serializer = EpisodioServicioSerializer(relaciones, many=True)
        return Response(serializer.data)
