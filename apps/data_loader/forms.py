from django import forms
from django.core.exceptions import ValidationError
from .models import ExcelUpload


class ExcelUploadForm(forms.ModelForm):
    """Formulario para subir archivos Excel"""
    
    class Meta:
        model = ExcelUpload
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.xlsx,.xls',
                'id': 'excelFile'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe el contenido del archivo Excel...'
            })
        }
        labels = {
            'file': 'Archivo Excel',
            'description': 'Descripción (Opcional)'
        }
    
    def clean_file(self):
        """Validaciones adicionales para el archivo"""
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError("Debe seleccionar un archivo.")
        
        # Validar extensión
        if not file.name.lower().endswith(('.xlsx', '.xls')):
            raise ValidationError("Solo se permiten archivos Excel (.xlsx, .xls)")
        
        # Validar tamaño (máximo 10MB)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError("El archivo no debe superar los 10MB")
        
        # Validar que no esté vacío
        if file.size == 0:
            raise ValidationError("El archivo está vacío")
        
        return file


class ExcelPreviewForm(forms.Form):
    """Formulario para confirmar carga después del preview"""
    
    upload_id = forms.UUIDField(widget=forms.HiddenInput())
    confirm_load = forms.BooleanField(
        required=True,
        label="Confirmo que deseo cargar estos datos a la base de datos",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )