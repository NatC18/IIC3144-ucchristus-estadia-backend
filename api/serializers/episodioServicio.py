"""
Serializers para el modelo relacion Episodio-Servicio
"""

from rest_framework import serializers

from api.models import EpisodioServicio
from api.serializers.servicio import ServicioSerializer


class EpisodioServicioSerializer(serializers.ModelSerializer):
    """
    Serializer completo para la relación Episodio-Servicio
    """
    servicio = ServicioSerializer(read_only=True)

    class Meta:
        model = EpisodioServicio
        fields = ["id", "episodio", "servicio", "fecha", "tipo", "orden_traslado"]
        read_only_fields = ["id"]
