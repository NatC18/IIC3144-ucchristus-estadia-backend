"""
Serializers para el modelo Cama
"""

from rest_framework import serializers

from api.models import Cama


class CamaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Cama
    """

    # Campos relacionados de solo lectura

    class Meta:
        model = Cama
        fields = [
            "id",
            "codigo_cama",
            "habitacion",
            "episodio_actual",
        ]
        read_only_fields = ["id", "episodio_actual"]
