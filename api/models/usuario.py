"""
Modelos para la aplicación API
"""
from django.db import models
from django.core.exceptions import ValidationError
import uuid




class Usuario(models.Model):
    """
    Modelo que representa un usuario en el sistema
    """
    
    # Campos
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rol = models.CharField(max_length=50)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    mail = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=128)  # Hashed password
    
    
    class Meta:
        db_table = 'usuarios'
        ordering = ['nombre']
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.nombre} )"
    