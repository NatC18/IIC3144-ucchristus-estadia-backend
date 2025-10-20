"""
Serializadores para el manejo de archivos Excel
"""
from rest_framework import serializers
from api.models import ArchivoCarga


class ArchivoCargaSerializer(serializers.ModelSerializer):
    """Serializador para mostrar información de archivos cargados"""
    
    porcentaje_completado = serializers.ReadOnlyField()
    
    class Meta:
        model = ArchivoCarga
        fields = [
            'id',
            'archivo',
            'tipo',
            'estado',
            'subido_en',
            'procesado_en',
            'filas_totales',
            'filas_procesadas',
            'filas_error',
            'errores',
            'porcentaje_completado',
            'subido_por',
        ]
        read_only_fields = [
            'id',
            'estado',
            'subido_en',
            'procesado_en',
            'filas_totales',
            'filas_procesadas',
            'filas_error',
            'errores',
            'porcentaje_completado',
            'subido_por',
        ]


class CargaArchivoSerializer(serializers.Serializer):
    """Serializador para la carga de archivos Excel"""
    
    TIPOS_CHOICES = [
        ('USERS', 'Usuarios'),
        ('PACIENTES', 'Pacientes'),
        ('CAMAS', 'Camas'),
        ('EPISODIOS', 'Episodios'),
        ('GESTIONES', 'Gestiones'),
    ]
    
    archivo = serializers.FileField(
        help_text="Archivo Excel (.xlsx, .xls) con los datos a procesar"
    )
    tipo = serializers.ChoiceField(
        choices=TIPOS_CHOICES,
        help_text="Tipo de datos contenidos en el archivo"
    )
    
    def validate_archivo(self, value):
        """Valida que el archivo sea un Excel válido"""
        if not value.name.lower().endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                "El archivo debe ser un Excel (.xlsx o .xls)"
            )
        
        # Validar tamaño (máximo 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "El archivo no puede ser mayor a 10MB"
            )
        
        return value


class EstadoProcesamientoSerializer(serializers.Serializer):
    """Serializador para consultar el estado de procesamiento"""
    
    id = serializers.IntegerField()
    estado = serializers.CharField()
    porcentaje_completado = serializers.FloatField()
    filas_totales = serializers.IntegerField()
    filas_procesadas = serializers.IntegerField()
    filas_exitosas = serializers.IntegerField()
    filas_errores = serializers.IntegerField()
    errores = serializers.JSONField()
    fecha_carga = serializers.DateTimeField()
    fecha_procesamiento = serializers.DateTimeField(allow_null=True)