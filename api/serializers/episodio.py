"""
Serializers para el modelo Episodio
"""

from rest_framework import serializers

from api.models import Episodio
from api.serializers.cama import CamaSerializer


class EpisodioSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Episodio
    Incluye datos completos de la cama asociada
    """

    cama = CamaSerializer(read_only=True)
    paciente = serializers.PrimaryKeyRelatedField(read_only=True)
    estancia_dias = serializers.IntegerField(read_only=True)
    alertas = serializers.SerializerMethodField()

    class Meta:
        model = Episodio
        fields = [
            "id",
            "paciente",
            "cama",
            "episodio_cmbd",
            "fecha_ingreso",
            "fecha_egreso",
            "tipo_actividad",
            "inlier_outlier_flag",
            "especialidad",
            "estancia_prequirurgica",
            "estancia_postquirurgica",
            "estancia_norma_grd",
            "prediccion_extension",
            "estancia_dias",
            "alertas",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "estancia_dias",
            "alertas",
        ]

    def get_alertas(self, obj):
        """
        Calcula las alertas para episodios activos (sin fecha_egreso).
        Retorna lista de strings con los tipos de alerta.
        """
        # Solo calcular alertas para episodios activos
        if obj.fecha_egreso:
            return []

        alertas = []

        # 1. Score Social Alto (>= 10)
        if obj.paciente and obj.paciente.score_social is not None:
            if obj.paciente.score_social >= 10:
                alertas.append("score_social_alto")

        # 2. Extensión Crítica (días > norma_grd * 4/3)
        if obj.estancia_norma_grd and obj.estancia_dias:
            umbral_critico = obj.estancia_norma_grd * (4 / 3)
            if obj.estancia_dias > umbral_critico:
                alertas.append("extension_critica")

        # 3. Predicción de Estadía Larga (modelo ML)
        if obj.prediccion_extension == 1:
            alertas.append("prediccion_estadia_larga")

        return alertas


class EpisodioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para creación de episodios
    """

    class Meta:
        model = Episodio
        fields = [
            "paciente",
            "cama",
            "fecha_ingreso",
            "tipo_actividad",
            "episodio_cmbd",
            "especialidad",
        ]


class EpisodioUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para actualización de episodios
    """

    class Meta:
        model = Episodio
        fields = [
            "cama",
            "fecha_egreso",
            "tipo_actividad",
            "inlier_outlier_flag",
            "especialidad",
            "estancia_prequirurgica",
            "estancia_postquirurgica",
            "estancia_norma_grd",
            "prediccion_extension",
        ]


class EpisodioListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar episodios con información básica
    """

    paciente_nombre = serializers.CharField(source="paciente.nombre", read_only=True)
    cama_codigo = serializers.CharField(source="cama.codigo_cama", read_only=True)
    alertas = serializers.SerializerMethodField()

    class Meta:
        model = Episodio
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "cama",
            "cama_codigo",
            "fecha_ingreso",
            "fecha_egreso",
            "tipo_actividad",
            "alertas",
        ]
        read_only_fields = ["id", "paciente_nombre", "cama_codigo", "alertas"]

    def get_alertas(self, obj):
        """Mismo método que EpisodioSerializer"""
        if obj.fecha_egreso:
            return []

        alertas = []

        if obj.paciente and obj.paciente.score_social is not None:
            if obj.paciente.score_social >= 10:
                alertas.append("score_social_alto")

        if obj.estancia_norma_grd and obj.estancia_dias:
            umbral_critico = obj.estancia_norma_grd * (4 / 3)
            if obj.estancia_dias > umbral_critico:
                alertas.append("extension_critica")

        if obj.prediccion_extension == 1:
            alertas.append("prediccion_estadia_larga")

        return alertas
