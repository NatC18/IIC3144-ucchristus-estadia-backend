"""
Serializers para el modelo Servicio
"""

from rest_framework import serializers

from api.models import EpisodioServicio, Servicio


class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ["id", "codigo", "descripcion"]
