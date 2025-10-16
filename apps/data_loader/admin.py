from django.contrib import admin
from .models import ExcelUpload


@admin.register(ExcelUpload)
class ExcelUploadAdmin(admin.ModelAdmin):
    """Administración simplificada de cargas Excel"""
    
    list_display = ['original_filename', 'status', 'uploaded_by', 'created_at']
    fields = ['file', 'description']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)