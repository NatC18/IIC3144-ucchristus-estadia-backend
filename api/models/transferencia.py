"""
Modelos para la aplicación API
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Transferencia(models.Model):
    """
    Modelo que representa una gestión de transferencia de un episodio en el sistema
    """

    # Opciones de motivos de traslado de gestion
    ESTADO_CHOICES = [
        ("ACEPTADO", "Aceptado"),
        ("CANCELADO", "Cancelado"),
        ("COMPLETADO", "Completado"),
        ("PENDIENTE", "Pendiente"),
        ("RECHAZADO", "Rechazado"),
    ]

    # Campos
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.OneToOneField(
        "Gestion", on_delete=models.CASCADE, related_name="transferencia"
    )
    estado = models.CharField(max_length=25)
    motivo_cancelacion = models.TextField(blank=True, null=True)
    motivo_rechazo = models.TextField(blank=True, null=True)
    tipo_traslado = models.CharField(max_length=50)
    motivo_traslado = models.CharField(max_length=50)
    centro_destinatario = models.CharField(max_length=100)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transferencias"
        ordering = ["estado"]
        verbose_name = "Transferencia"
        verbose_name_plural = "Transferencias"

    def __str__(self):
        return f"Transferencia {self.id} - Gestión: {self.gestion.id}"
