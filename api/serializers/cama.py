"""
Serializers para el modelo Cama
"""

from rest_framework import serializers

from api.models import Cama


class CamaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Cama
    Usado en contextos donde se necesita información básica de la cama
    sin referencias circulares a episodios
    """

    class Meta:
        model = Cama
        fields = [
            "id",
            "codigo_cama",
            "habitacion",
        ]
        read_only_fields = ["id"]
