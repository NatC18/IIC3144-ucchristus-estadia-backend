"""
Modelos para la aplicación API
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Gestion(models.Model):
    """
    Modelo que representa una gestión de un episodio en el sistema
    """

    # Opciones de estados de gestion
    ESTADO_CHOICES = [
        ("INICIADA", "Iniciada"),
        ("EN_PROGRESO", "En Progreso"),
        ("COMPLETADA", "Completada"),
        ("CANCELADA", "Cancelada"),
    ]

    TIPO_GESTION_CHOICES = [
        ("HOMECARE_UCCC", "Homecare UCCC"),
        ("HOMECARE", "Homecare"),
        ("TRASLADO", "Traslado"),
        ("ACTIVACION_BENEFICIO_ISAPRE", "Activación Beneficio Isapre"),
        ("AUTORIZACION_PROCEDIMIENTO", "Autorización Procedimiento"),
        ("COBERTURA", "Cobertura"),
        ("CORTE_CUENTAS", "Corte Cuentas"),
        ("EVALUACION_OTRO_FINANCIAMIENTO", "Evaluación de otro financiamiento"),
        (
            "ACTUALIZACION_ESTADO_PACIENTE",
            "Actualización de estado paciente solicitado por prestadores",
        ),
        ("ASIGNACION_CENTRO_DIALISIS", "Asignación de Centro de Dialisis"),
        ("MANEJO_AMBULATORIO", "Manejo ambulatorio"),
        ("INGRESO_CUIDADOS_PALIATIVOS", "Ingreso de Cuidados Paliativos"),
        (
            "EVALUACION_BENEFICIO_GESTION_INTERNA",
            "Evaluación de beneficio gestión interna",
        ),
        ("GESTION_CLINICA", "Gestión Clínica"),
    ]

    # Opciones para traslado
    ESTADO_TRASLADO_CHOICES = [
        ("ACEPTADO", "Aceptado"),
        ("CANCELADO", "Cancelado"),
        ("COMPLETADO", "Completado"),
        ("PENDIENTE", "Pendiente"),
        ("RECHAZADO", "Rechazado"),
    ]

    TIPO_TRASLADO_CHOICES = [
        ("SALUD_MENTAL", "Salud Mental"),
        ("URGENCIA", "Urgencia"),
        ("HOSPITALIZADO_EXTERNO", "Hospitalizado Externo (Non UC)"),
        ("HOSPITALIZADO_INTERNO", "Hospitalizado Interno (UC)"),
    ]

    NIVEL_ATENCION_CHOICES = [
        ("MEDICINA_QUIRURGICA", "Medicina Quirúrgica (MQ)"),
        ("SALUD_MENTAL", "Salud Mental"),
        ("CUIDADOS_INTENSIVOS", "Cuidados Intensivos (UCI)"),
        ("INTERMEDIO", "Intermedio"),
        ("NEONATOLOGIA", "Neonatología"),
        ("OBSTETRICIA", "Obstetricia"),
        ("URGENCIA", "Urgencia"),
    ]

    TIPO_SOLICITUD_CHOICES = [
        ("CONSULTA", "Consulta"),
        ("ADMISION_DIRECTA", "Admisión Directa"),
        ("TRASLADO_INGRESO", "Traslado de Ingreso"),
        ("TRASLADO_SALIDA", "Traslado de Salida"),
    ]

    # Campos
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    episodio = models.ForeignKey(
        "Episodio", on_delete=models.CASCADE, related_name="gestiones"
    )
    usuario = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="gestiones",
        null=True,
        blank=True,
    )
    tipo_gestion = models.CharField(max_length=50, choices=TIPO_GESTION_CHOICES)
    estado_gestion = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    informe = models.TextField(blank=True, null=True)

    # Campos de traslado (todos opcionales)
    estado_traslado = models.CharField(
        max_length=50,
        choices=ESTADO_TRASLADO_CHOICES,
        blank=True,
        null=True,
        help_text="Estado del traslado si esta gestión es de tipo TRASLADO",
    )
    tipo_traslado = models.CharField(
        max_length=50,
        choices=TIPO_TRASLADO_CHOICES,
        blank=True,
        null=True,
        help_text="Tipo de traslado",
    )
    motivo_traslado = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo o razón del traslado",
    )
    centro_destinatario = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Centro o institución de destino",
    )
    tipo_solicitud_traslado = models.CharField(
        max_length=50,
        choices=TIPO_SOLICITUD_CHOICES,
        blank=True,
        null=True,
        help_text="Tipo de solicitud de traslado",
    )
    nivel_atencion_traslado = models.CharField(
        max_length=50,
        choices=NIVEL_ATENCION_CHOICES,
        blank=True,
        null=True,
        help_text="Nivel de atención requerido en el traslado",
    )
    motivo_rechazo_traslado = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo del rechazo si el traslado fue rechazado",
    )
    motivo_cancelacion_traslado = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo de la cancelación si el traslado fue cancelado",
    )

    fecha_finalizacion_traslado = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha de finalización del traslado",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gestiones"
        ordering = ["fecha_inicio"]
        verbose_name = "Gestion"
        verbose_name_plural = "Gestiones"

    def __str__(self):
        return f"Gestión {self.id} - Episodio: {self.episodio.id}"

    @property
    def duracion_dias(self):
        """Calcular duración de la gestión en días"""
        if self.fecha_fin and self.fecha_inicio:
            return (self.fecha_fin - self.fecha_inicio).days
        elif self.fecha_inicio:
            from django.utils import timezone
            today = timezone.now()
            return (today - self.fecha_inicio).days
        else:
            return None
