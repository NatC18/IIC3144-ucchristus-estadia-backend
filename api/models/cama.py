"""
Modelos para la aplicación API
"""
from django.db import models
from django.core.exceptions import ValidationError
import uuid


class Cama(models.Model):
    """
    Modelo que representa una cama en el sistema
    """
    
    
    # Campos
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_cama = models.CharField(max_length=20)
    habitacion = models.CharField(max_length=20)

    
    class Meta:
        db_table = 'camas'
        ordering = ['codigo_cama']
        verbose_name = 'Cama'
        verbose_name_plural = 'Camas'


    def __str__(self):
        return f"Cama {self.codigo_cama}"
    
    @property
    def episodio_actual(self):
        """Retorna el episodio activo asociado a esta cama, si existe"""
        return self.episodios.filter(fecha_egreso__isnull=True).first()

    
    