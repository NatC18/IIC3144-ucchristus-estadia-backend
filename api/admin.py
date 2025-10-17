"""
Configuración del admin para la aplicación API
"""

from django.contrib import admin

from api.models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Paciente
    """

    list_display = ["nombre", "rut", "sexo", "edad", "prevision", "created_at"]
    list_filter = ["sexo", "prevision", "created_at"]
    search_fields = ["nombre", "rut"]
    readonly_fields = ["id", "edad", "created_at", "updated_at"]

    fieldsets = (
        (
            "Información Personal",
            {"fields": ("rut", "nombre", "sexo", "fecha_nacimiento")},
        ),
        ("Información Médica", {"fields": ("prevision", "convenio", "score_social")}),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def edad(self, obj):
        """Mostrar edad en el listado"""
        return obj.edad

    edad.short_description = "Edad"
