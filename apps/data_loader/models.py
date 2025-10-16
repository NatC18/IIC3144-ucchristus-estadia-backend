from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import uuid
import os

User = get_user_model()


def upload_to_excel(instance, filename):
    """Función para organizar uploads de Excel por fecha"""
    from datetime import date
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Usar fecha actual si instance.created_at aún no existe
    upload_date = instance.created_at.date() if instance.created_at else date.today()
    return os.path.join('uploads/excel', str(upload_date), filename)


class ExcelUpload(models.Model):
    """Modelo para gestionar archivos Excel subidos por administradores"""
    
    STATUS_CHOICES = [
        ('uploaded', 'Subido'),
        ('processing', 'Procesando'),
        ('processed', 'Procesado'),
        ('error', 'Error'),
        ('loaded', 'Cargado a BD'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Archivo
    file = models.FileField(
        upload_to=upload_to_excel,
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        help_text="Solo archivos Excel (.xlsx, .xls)"
    )
    original_filename = models.CharField(max_length=255)
    
    # Metadatos de procesamiento
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    description = models.TextField(
        blank=True, 
        help_text="Descripción del contenido del archivo"
    )
    
    # Información de procesamiento
    total_rows = models.PositiveIntegerField(null=True, blank=True)
    processed_rows = models.PositiveIntegerField(null=True, blank=True)
    error_rows = models.PositiveIntegerField(null=True, blank=True)
    error_log = models.JSONField(default=dict, blank=True)
    
    # Datos procesados (temporal)
    preview_data = models.JSONField(default=dict, blank=True)
    headers = models.JSONField(default=list, blank=True)
    
    # Auditoría
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Carga de Excel"
        verbose_name_plural = "Cargas de Excel"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.original_filename} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            self.original_filename = self.file.name
        
        # Llamar al save original
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Procesar automáticamente si es un archivo nuevo
        if is_new and self.file:
            self.process_excel_async()
    
    def process_excel_async(self):
        """Procesar Excel de forma asíncrona (simulada)"""
        try:
            from .services import ExcelProcessor
            processor = ExcelProcessor(self)
            result = processor.process_file()
            return result
        except Exception as e:
            self.status = 'error'
            self.error_log = {'processing_error': str(e)}
            self.save(update_fields=['status', 'error_log'])
    
    @property
    def file_size_mb(self):
        """Retorna el tamaño del archivo en MB"""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0
    
    @property
    def success_rate(self):
        """Calcula la tasa de éxito del procesamiento"""
        if self.total_rows and self.processed_rows is not None:
            return round((self.processed_rows / self.total_rows) * 100, 1)
        return 0