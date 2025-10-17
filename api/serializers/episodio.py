"""
Serializers para el modelo Episodio
"""
from rest_framework import serializers
from api.models import Episodio


class EpisodioSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Episodio
    """
    class Meta:
        model = Episodio
        fields = [
            'id',
            'paciente',
            'cama',
            'episodio_cmbd',
            'fecha_ingreso',
            'fecha_egreso',
            'tipo_actividad',
            'inlier_outlier_flag',
            'especialidad',
            'estancia_prequirurgica',
            'estancia_postquirurgica',
            'estancia_norma_grd',
            'estancia_dias',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'estancia_dias']

class EpisodioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para creación de episodios
    """
    class Meta:
        model = Episodio
        fields = [
            'paciente',
            'cama',
            'fecha_ingreso',
            'tipo_actividad',
            'episodio_cmbd',
            'especialidad',
        ]
 
class EpisodioUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para actualización de episodios
    """
    class Meta:
        model = Episodio
        fields = [
            'cama',
            'fecha_egreso',
            'tipo_actividad',
            'inlier_outlier_flag',
            'especialidad',
            'estancia_prequirurgica',
            'estancia_postquirurgica',
            'estancia_norma_grd',
        ]

class EpisodioListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar episodios con información básica
    """
    paciente_nombre = serializers.CharField(source='paciente.nombre', read_only=True)
    cama_codigo = serializers.CharField(source='cama.codigo_cama', read_only=True)
    
    class Meta:
        model = Episodio
        fields = [
            'id',
            'paciente',
            'paciente_nombre',
            'cama',
            'cama_codigo',
            'fecha_ingreso',
            'fecha_egreso',
            'tipo_actividad',
        ]
        read_only_fields = ['id', 'paciente_nombre', 'cama_codigo']

        