"""
Modelos para la aplicación API
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Episodio(models.Model):
    """
    Modelo que representa un episodio clínico en el sistema
    """

    # Campos

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        "Paciente", on_delete=models.CASCADE, related_name="episodios"
    )
    cama = models.ForeignKey(
        "Cama",
        on_delete=models.SET_NULL,
        related_name="episodios",
        null=True,
        blank=True,
    )
    episodio_cmbd = models.IntegerField()
    fecha_ingreso = models.DateTimeField()
    fecha_egreso = models.DateTimeField(blank=True, null=True)
    tipo_actividad = models.CharField(max_length=100)
    inlier_outlier_flag = models.CharField(max_length=10, blank=True, null=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    estancia_prequirurgica = models.FloatField(blank=True, null=True)
    estancia_postquirurgica = models.FloatField(blank=True, null=True)
    estancia_norma_grd = models.FloatField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "episodios"
        ordering = ["fecha_ingreso"]
        verbose_name = "Episodio"
        verbose_name_plural = "Episodios"

    def __str__(self):
        return f"Episodio {self.id} - Paciente: {self.paciente.nombre}"

    def save(self, *args, **kwargs):
        # Validar que la cama no esté asignada a otro episodio activo (solo si hay cama)
        if self.cama and not self.fecha_egreso:
            conflicto = (
                Episodio.objects.filter(cama=self.cama, fecha_egreso__isnull=True)
                .exclude(id=self.id)
                .exists()
            )
            if conflicto:
                raise ValidationError(
                    f"La cama {self.cama.codigo_cama} ya está asignada a otro episodio activo."
                )
        
        # Siempre llamar a super().save() para guardar el objeto
        super().save(*args, **kwargs)

    @property
    def estancia_dias(self):
        """Calcular días de estancia del episodio"""
        if self.fecha_egreso and self.fecha_ingreso:
            return (self.fecha_egreso - self.fecha_ingreso).days
        else:
            from datetime import date

            today = date.now()
            return (today - self.fecha_ingreso).days
