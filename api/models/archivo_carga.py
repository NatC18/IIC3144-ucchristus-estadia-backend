import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ArchivoCarga(models.Model):
    """
    Modelo para el tracking de archivos Excel subidos y su procesamiento
    """
    
    ESTADO_CHOICES = [
        ('SUBIDO', 'Archivo Subido'),
        ('PROCESANDO', 'Procesando'),
        ('COMPLETADO', 'Procesamiento Completado'),
        ('ERROR', 'Error en Procesamiento'),
        ('PARCIAL', 'Procesamiento Parcial'),
    ]
    
    TIPO_CHOICES = [
        ('users', 'Usuarios'),
        ('pacientes', 'Pacientes'),
        ('camas', 'Camas'),
        ('episodios', 'Episodios'),
        ('gestiones', 'Gestiones'),
        ('servicios', 'Servicios'),
        ('mixto', 'Datos Mixtos'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255, help_text="Nombre original del archivo")
    archivo = models.FileField(upload_to="uploads/excel/")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, help_text="Tipo de datos en el archivo")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='SUBIDO')
    
    # Timestamps
    fecha_carga = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    
    # Resultados del procesamiento
    filas_totales = models.IntegerField(null=True, blank=True, help_text="Total de filas en el archivo")
    filas_procesadas = models.IntegerField(default=0, help_text="Filas procesadas exitosamente")
    filas_exitosas = models.IntegerField(default=0, help_text="Filas procesadas sin errores")
    filas_errores = models.IntegerField(default=0, help_text="Filas con errores")
    
    # Logs y errores
    log_procesamiento = models.JSONField(default=dict, blank=True, help_text="Log detallado del procesamiento")
    errores = models.JSONField(default=list, blank=True, help_text="Lista de errores encontrados")
    
    # Usuario que subió el archivo
    usuario = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='archivos_subidos'
    )

    class Meta:
        verbose_name = "Archivo de Carga"
        verbose_name_plural = "Archivos de Carga"
        ordering = ['-fecha_carga']

    def clean(self):
        """Validaciones del modelo"""
        if self.archivo and not self.archivo.name.lower().endswith(('.xlsx', '.xls')):
            raise ValidationError("Solo se permiten archivos Excel (.xlsx, .xls)")

    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_display()} ({self.estado})"
    
    @property
    def porcentaje_completado(self):
        """Calcula el porcentaje de filas procesadas"""
        if not self.filas_totales or self.filas_totales == 0:
            return 0
        return round((self.filas_procesadas / self.filas_totales) * 100, 2)
    
    @property
    def tiene_errores(self):
        """Indica si hubo errores durante el procesamiento"""
        return self.filas_errores > 0 or len(self.errores) > 0
    
    def agregar_error(self, fila, error, detalle=None):
        """Método para agregar errores durante el procesamiento"""
        error_info = {
            'fila': fila,
            'error': str(error),
            'timestamp': timezone.now().isoformat(),
        }
        if detalle:
            error_info['detalle'] = detalle
            
        self.errores.append(error_info)
        self.save(update_fields=['errores'])
    
    def actualizar_progreso(self, filas_procesadas, filas_errores=0):
        """Actualiza el progreso del procesamiento"""
        self.filas_procesadas = filas_procesadas
        self.filas_exitosas = filas_procesadas
        self.filas_errores = filas_errores
        
        # Calcular total de filas intentadas (procesadas + errores)
        filas_intentadas = filas_procesadas + filas_errores
        
        # Determinar estado final cuando se han intentado todas las filas
        if self.filas_totales and filas_intentadas >= self.filas_totales:
            if filas_errores == 0:
                self.estado = 'COMPLETADO'
            elif filas_procesadas == 0:
                # Si todas las filas tuvieron errores
                self.estado = 'ERROR' 
            else:
                # Si algunas filas se procesaron y otras tuvieron errores
                self.estado = 'PARCIAL'
        
        self.save(update_fields=['filas_procesadas', 'filas_exitosas', 'filas_errores', 'estado'])
