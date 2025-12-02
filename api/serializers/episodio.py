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
    semaforo_riesgo = serializers.SerializerMethodField()

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
            "probabilidad_extension",
            "ignorar",
            "estancia_dias",
            "alertas",
            "semaforo_riesgo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "estancia_dias",
            "alertas",
            "semaforo_riesgo",
        ]

    def get_semaforo_riesgo(self, obj):
        """
        Calcula el color del semáforo según probabilidad de extensión.
        Retorna dict con 'color' y 'probabilidad'.
        - gray: episodio ya se extendió (tiene extensión crítica)
        - green: probabilidad baja (< 0.3)
        - yellow: probabilidad media (0.3 - 0.45)
        - red: probabilidad alta (>= 0.45)
        """
        # Si ya tiene extensión crítica, mostrar gris
        if obj.estancia_norma_grd and obj.estancia_dias:
            umbral_critico = obj.estancia_norma_grd * (4 / 3)
            if obj.estancia_dias > umbral_critico:
                return {"color": "gray", "probabilidad": obj.probabilidad_extension}

        # Si no tiene probabilidad, mostrar gris también
        if obj.probabilidad_extension is None:
            return {"color": "gray", "probabilidad": None}

        # Clasificar según rangos de probabilidad
        prob = obj.probabilidad_extension
        if prob >= 0.45:
            return {"color": "red", "probabilidad": prob}  # Alto riesgo
        elif prob >= 0.3:
            return {"color": "yellow", "probabilidad": prob}  # Riesgo medio
        else:
            return {"color": "green", "probabilidad": prob}  # Bajo riesgo

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
        tiene_extension_critica = False
        if obj.estancia_norma_grd and obj.estancia_dias:
            umbral_critico = obj.estancia_norma_grd * (4 / 3)
            if obj.estancia_dias > umbral_critico:
                alertas.append("extension_critica")
                tiene_extension_critica = True

        # 3. Predicción de Estadía Larga (modelo ML)
        # Solo mostrar si NO tiene extensión crítica (no se ha pasado aún)
        if obj.prediccion_extension == 1 and not tiene_extension_critica:
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
            "ignorar",
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
            "probabilidad_extension",
            "ignorar",
        ]


class EpisodioListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar episodios con información básica
    """

    paciente_nombre = serializers.CharField(source="paciente.nombre", read_only=True)
    cama_codigo = serializers.CharField(source="cama.codigo_cama", read_only=True)
    alertas = serializers.SerializerMethodField()
    semaforo_riesgo = serializers.SerializerMethodField()

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
            "ignorar",
            "alertas",
            "semaforo_riesgo",
        ]
        read_only_fields = [
            "id",
            "paciente_nombre",
            "cama_codigo",
            "alertas",
            "semaforo_riesgo",
        ]

    def get_semaforo_riesgo(self, obj):
        """Mismo método que EpisodioSerializer"""
        if obj.estancia_norma_grd and obj.estancia_dias:
            umbral_critico = obj.estancia_norma_grd * (4 / 3)
            if obj.estancia_dias > umbral_critico:
                return {"color": "gray", "probabilidad": obj.probabilidad_extension}

        if obj.probabilidad_extension is None:
            return {"color": "gray", "probabilidad": None}

        prob = obj.probabilidad_extension
        if prob >= 0.45:
            return {"color": "red", "probabilidad": prob}
        elif prob >= 0.3:
            return {"color": "yellow", "probabilidad": prob}
        else:
            return {"color": "green", "probabilidad": prob}

    def get_alertas(self, obj):
        """Mismo método que EpisodioSerializer"""
        if obj.fecha_egreso:
            return []

        alertas = []

        if obj.paciente and obj.paciente.score_social is not None:
            if obj.paciente.score_social >= 10:
                alertas.append("score_social_alto")

        tiene_extension_critica = False
        if obj.estancia_norma_grd and obj.estancia_dias:
            umbral_critico = obj.estancia_norma_grd * (4 / 3)
            if obj.estancia_dias > umbral_critico:
                alertas.append("extension_critica")
                tiene_extension_critica = True

        if obj.prediccion_extension == 1 and not tiene_extension_critica:
            alertas.append("prediccion_estadia_larga")

        return alertas
