"""
Modelos para la aplicación API
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models


def validar_rut(rut):
    """
    Validación básica de RUT chileno
    """
    if not rut:
        raise ValidationError("RUT es requerido")

    # Formato básico: XX.XXX.XXX-X
    import re

    if not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", rut):
        raise ValidationError("Formato de RUT inválido. Use: XX.XXX.XXX-X")


class Paciente(models.Model):
    """
    Modelo que representa un paciente en el sistema
    """

    # Choices
    SEXO_CHOICES = [
        ("M", "Hombre"),
        ("F", "Mujer"),
        ("O", "Otro"),
    ]

    PREVISION_CHOICES = [
        ("FONASA", "FONASA"),
        ("ISAPRE", "ISAPRE"),
        ("PARTICULAR", "PARTICULAR"),
        ("OTRO", "OTRO"),
    ]

    # Campos

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[validar_rut],
        help_text="Formato: XX.XXX.XXX-X",
    )
    nombre = models.CharField(max_length=200)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    fecha_nacimiento = models.DateField()
    prevision_1 = models.CharField(max_length=20, blank=True, null=True)
    prevision_2 = models.CharField(max_length=20, blank=True, null=True)
    convenio = models.CharField(max_length=100, blank=True, null=True)
    score_social = models.IntegerField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pacientes"
        ordering = ["nombre"]
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"

    def __str__(self):
        return f"{self.nombre} ({self.rut})"

    @property
    def edad(self):
        """Calcular edad del paciente"""
        from datetime import date

        today = date.today()
        return (
            today.year
            - self.fecha_nacimiento.year
            - (
                (today.month, today.day)
                < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        )
