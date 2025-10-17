"""
Modelos para la aplicación API
"""
from django.db import models
from django.core.exceptions import ValidationError
import uuid



class Gestion(models.Model):
    """
    Modelo que representa una gestión de un episodio en el sistema
    """
    # Opciones de estados de gestion
    ESTADO_CHOICES = [
        ('INICIADA', 'Iniciada'),
        ('EN_PROGRESO', 'En Progreso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    TIPO_GESTION_CHOICES = [
        ('HOMECARE_UCCC', 'Homecare UCCC'),
        ('HOMECARE', 'Homecare'),
        ('TRASLADO', 'Traslado'),
        ('ACTIVACION_BENEFICIO_ISAPRE', 'Activación Beneficio Isapre'),
        ('AUTORIZACION_PROCEDIMIENTO', 'Autorización Procedimiento'),
        ('COBERTURA', 'Cobertura'),
        ('CORTE_CUENTAS', 'Corte Cuentas'),
        ('EVALUACION_OTRO_FINANCIAMIENTO', 'Evaluación de otro financiamiento'),
        ('ACTUALIZACION_ESTADO_PACIENTE', 'Actualización de estado paciente solicitado por prestadores'),
        ('ASIGNACION_CENTRO_DIALISIS', 'Asignación de Centro de Dialisis'),
        ('MANEJO_AMBULATORIO', 'Manejo ambulatorio'),
        ('INGRESO_CUIDADOS_PALIATIVOS', 'Ingreso de Cuidados Paliativos'),
        ('EVALUACION_BENEFICIO_GESTION_INTERNA', 'Evaluación de beneficio gestión interna'),
        ('GESTION_CLINICA', 'Gestión Clínica'),
    ]

    # Campos
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    episodio = models.ForeignKey('Episodio', on_delete=models.CASCADE, related_name='gestiones')
    usuario = models.ForeignKey('Usuario', on_delete=models.SET_NULL, related_name='gestiones', null=True, blank=True)
    tipo_gestion = models.CharField(max_length=50, choices=TIPO_GESTION_CHOICES)
    estado_gestion = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    informe = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'gestiones'
        ordering = ['fecha_inicio']
        verbose_name = 'Gestion'
        verbose_name_plural = 'Gestiones'

    def __str__(self):
        return f"Gestión {self.id} - Episodio: {self.episodio.id}"

    @property
    def duracion_dias(self):
        """Calcular duración de la gestión en días"""
        if self.fecha_fin and self.fecha_inicio:
            return (self.fecha_fin - self.fecha_inicio).days
        else:
            from datetime import datetime
            today = datetime.now()
            return (today - self.fecha_inicio).days if self.fecha_inicio else None