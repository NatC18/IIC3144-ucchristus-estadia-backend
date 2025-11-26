"""
Modelos para la aplicación API
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models


class EpisodioServicio(models.Model):
    """
    Modelo que representa relaciones entre servicios y episodios en el sistema
    """

    # Campos

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    servicio = models.ForeignKey(
        "Servicio", on_delete=models.CASCADE, related_name="episodios"
    )
    episodio = models.ForeignKey(
        "Episodio", on_delete=models.CASCADE, related_name="servicios"
    )
    fecha = models.DateTimeField(null=True, blank=True)
    tipo = models.CharField(max_length=20)
    orden_traslado = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "episodios_servicio"
        ordering = ["fecha"]
        verbose_name = "Episodio Servicio"
        verbose_name_plural = "Episodios Servicio"

    def __str__(self):
        return f"Episodio: {self.episodio.id}, Servicio: {self.servicio.codigo}, fecha: {self.fecha}, Orden: {self.orden_traslado}"
