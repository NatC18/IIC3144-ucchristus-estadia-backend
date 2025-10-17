"""
Serializers para el modelo Servicio
"""
from rest_framework import serializers
from api.models import Servicio


class ServicioSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Servicio
    """
    class Meta:
        model = Servicio
        fields = [
            'id',
            'codigo',
            'descripcion',
        ]
        read_only_fields = ['id']

