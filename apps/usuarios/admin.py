"""
Configuración del admin para usuarios.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Configuración del admin para el modelo Usuario personalizado"""
    
    list_display = ('username', 'email', 'nombre_completo', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'nombre_completo')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('nombre_completo', 'telefono', 'auth0_user_id')
        }),
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
