"""
Serializers para el modelo Paciente
"""
from rest_framework import serializers
from api.models import Paciente


class PacienteSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Paciente
    """
    edad = serializers.ReadOnlyField()  # Campo calculado
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'rut',
            'nombre', 
            'sexo',
            'fecha_nacimiento',
            'edad',
            'prevision_1',
            'prevision_2',
            'convenio',
            'score_social',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'edad']
    
    def validate_rut(self, value):
        """
        Validación adicional para el RUT
        """
        if value:
            value = value.upper()  # Normalizar K mayúscula
        return value


class PacienteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para creación de pacientes
    """
    class Meta:
        model = Paciente
        fields = [
            'rut',
            'nombre', 
            'sexo',
            'fecha_nacimiento',
            'prevision_1',
            'prevision_2',
            'convenio',
            'score_social',
        ]
    
    def validate_rut(self, value):
        """
        Validación adicional para el RUT en creación
        """
        if value:
            value = value.upper()
        return value


class PacienteListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listado de pacientes
    """
    edad = serializers.ReadOnlyField()
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'rut',
            'nombre', 
            'sexo',
            'edad',
            'prevision_1',
            'prevision_2',
        ]