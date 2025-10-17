"""
Serializers para el modelo Transferencia
"""
from rest_framework import serializers
from api.models import Transferencia


class TransferenciaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Transferencia
    """
    class Meta:
        model = Transferencia
        fields = [
            'id',
            'gestion',
            'estado',
            'motivo_cancelacion',
            'motivo_rechazo',
            'tipo_traslado',
            'motivo_traslado',
            'centro_destinatario',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TransferenciaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para creación de transferencias
    """
    class Meta:
        model = Transferencia
        fields = [
            'gestion',
            'estado',
            'tipo_traslado',
            'motivo_traslado',
            'centro_destinatario',
        ]
    

class TransferenciaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para actualización de transferencias
    """
    class Meta:
        model = Transferencia
        fields = [
            'estado',
            'motivo_cancelacion',
            'motivo_rechazo',
        ]

    def validate(self, attrs):
        """
        Validación condicional basada en el estado de la transferencia
        """
        estado = attrs.get('estado', None)
        if estado == Transferencia.ESTADO_CANCELADA and not attrs.get('motivo_cancelacion'):
            raise serializers.ValidationError("El motivo de cancelación es obligatorio si el estado es 'cancelada'.")
        if estado == Transferencia.ESTADO_RECHAZADA and not attrs.get('motivo_rechazo'):
            raise serializers.ValidationError("El motivo de rechazo es obligatorio si el estado es 'rechazada'.")
        return attrs

class TransferenciaListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listar transferencias
    """
    class Meta:
        model = Transferencia
        fields = [
            'id',
            'gestion',
            'estado',
            'tipo_traslado',
            'motivo_traslado',
            'centro_destinatario',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


