"""
Serializers para el modelo Nota
"""

from rest_framework import serializers

from api.models import Nota


class NotaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Nota
    """

    usuario_nombre = serializers.SerializerMethodField()
    gestion_id = serializers.UUIDField(source="gestion.id", read_only=True)

    class Meta:
        model = Nota
        fields = [
            "id",
            "gestion_id",
            "usuario",
            "usuario_nombre",
            "descripcion",
            "fecha_nota",
            "estado",
        ]
        read_only_fields = ["id", "fecha_nota"]

    def get_usuario_nombre(self, obj):
        """
        Retorna el nombre completo del usuario si existe
        """
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return None


class NotaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para creación de notas
    """

    class Meta:
        model = Nota
        fields = [
            "gestion",
            "usuario",
            "descripcion",
            "estado",
        ]

    def validate(self, data):
        """
        Validación adicional para notas
        """
        if not data.get("descripcion") or not data["descripcion"].strip():
            raise serializers.ValidationError(
                {"descripcion": "La descripción no puede estar vacía"}
            )

        if not data.get("estado") or not data["estado"].strip():
            raise serializers.ValidationError(
                {"estado": "El estado no puede estar vacío"}
            )

        return data


class NotaListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listado de notas
    """

    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Nota
        fields = [
            "id",
            "usuario_nombre",
            "descripcion",
            "fecha_nota",
            "estado",
        ]

    def get_usuario_nombre(self, obj):
        """
        Retorna el nombre completo del usuario si existe
        """
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return None


class NotaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualización de notas
    """

    class Meta:
        model = Nota
        fields = [
            "usuario",
            "descripcion",
            "estado",
        ]

    def validate(self, data):
        """
        Validación adicional para actualización
        """
        if "descripcion" in data and (
            not data["descripcion"] or not data["descripcion"].strip()
        ):
            raise serializers.ValidationError(
                {"descripcion": "La descripción no puede estar vacía"}
            )

        if "estado" in data and (not data["estado"] or not data["estado"].strip()):
            raise serializers.ValidationError(
                {"estado": "El estado no puede estar vacío"}
            )

        return data
