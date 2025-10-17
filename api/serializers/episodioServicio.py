"""
Serializers para el modelo relacion Episodio-Servicio
"""
from rest_framework import serializers
from api.models import EpisodioServicio


class EpisodioServicioSerializer(serializers.ModelSerializer):
    """
    Serializer completo para la relación Episodio-Servicio
    """
    class Meta:
        model = EpisodioServicio
        fields = [
            'id',
            'episodio',
            'servicio',
            'fecha',
            'tipo',
            'orden_traslado'
        ]
        read_only_fields = ['id']

