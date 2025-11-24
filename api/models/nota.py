"""
Modelo de Notas de una gestion
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Nota(models.Model):
    """
    Modelo que representa una nota de una gestion
    relación  una gestion tiene muchas notas, una nota pertenece a una gestion
    """

    # Campos

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.ForeignKey(
        "Gestion", on_delete=models.CASCADE, related_name="notas"
    )
    usuario = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="notas",
        null=True,
        blank=True,
    )
    descripcion = models.TextField()
    fecha_nota = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50)



    class Meta:
        db_table = "notas"
        ordering = ["-fecha_nota"]
        verbose_name = "Nota"
        verbose_name_plural = "Notas"

    def __str__(self):
        return f"Nota {self.id} - Gestion: {self.gestion.id}"
    
    def clean(self):
        # Validar que la descripcion no este vacia
        if not self.descripcion:
            raise ValidationError("La descripcion no puede estar vacia")
        # Validar que el estado no este vacio
        if not self.estado:
            raise ValidationError("El estado no puede estar vacio") 