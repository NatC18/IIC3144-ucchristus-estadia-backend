"""
Serializers para el modelo Usuario
"""
from rest_framework import serializers
from api.models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Usuario
    """
    class Meta:
        model = Usuario
        fields = [
            'id',
            'nombre',
            'rut',
            'apellido',
            'mail',
            'rol',
            'contrasena',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UsuarioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para creación de usuarios
    """
    class Meta:
        model = Usuario
        fields = [
            'nombre',
            'rut',
            'apellido',
            'mail',
            'rol',
            'contrasena',
        ]
    
class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para actualización de usuarios
    """
    class Meta:
        model = Usuario
        fields = [
            'nombre',
            'apellido',
            'mail',
            'rol',
            'contrasena',
        ]
    
