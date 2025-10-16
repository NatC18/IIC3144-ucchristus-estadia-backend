"""
Modelos para la gestión de usuarios con Auth0.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser
    para integración con Auth0.
    """
    
    # Campo para almacenar el ID único de Auth0
    auth0_user_id = models.CharField(
        max_length=255, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="ID único del usuario en Auth0"
    )
    
    # Información adicional del perfil
    nombre_completo = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Nombre completo del usuario"
    )
    
    telefono = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Número de teléfono"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    @property
    def nombre_display(self):
        """Retorna el nombre para mostrar, priorizando nombre_completo"""
        return self.nombre_completo or f"{self.first_name} {self.last_name}".strip() or self.username
