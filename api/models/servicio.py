"""
Modelos para la aplicación API
"""
from django.db import models
from django.core.exceptions import ValidationError
import uuid

class Servicio(models.Model):
    """
    Modelo que representa un servicio ocupado por episodios en el sistema
    """
    
    
    # Campos
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'servicios'
        ordering = ['codigo']
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return f"{self.codigo} ({self.descripcion})"

