"""
Serializers para el modelo Gestion
"""

from rest_framework import serializers

from api.models import Gestion


class GestionSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Gestion
    """

    # Campos relacionados de solo lectura
    episodio_id = serializers.UUIDField(source="episodio.id", read_only=True)
    usuario_nombre = serializers.SerializerMethodField()
    tipo_gestion_display = serializers.CharField(
        source="get_tipo_gestion_display", read_only=True
    )
    estado_gestion_display = serializers.CharField(
        source="get_estado_gestion_display", read_only=True
    )

    class Meta:
        model = Gestion
        fields = [
            "id",
            "episodio",
            "episodio_id",
            "usuario",
            "usuario_nombre",
            "tipo_gestion",
            "tipo_gestion_display",
            "estado_gestion",
            "estado_gestion_display",
            "fecha_inicio",
            "fecha_fin",
            "informe",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_usuario_nombre(self, obj):
        """
        Retorna el nombre completo del usuario si existe
        """
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return None


class GestionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para creación de gestiones
    """

    class Meta:
        model = Gestion
        fields = [
            "episodio",
            "usuario",
            "tipo_gestion",
            "estado_gestion",
            "fecha_inicio",
            "fecha_fin",
            "informe",
        ]

    def validate(self, data):
        """
        Validación adicional para gestiones
        """
        # Validar que fecha_fin sea posterior a fecha_inicio si existe
        if data.get("fecha_fin") and data.get("fecha_inicio"):
            if data["fecha_fin"] < data["fecha_inicio"]:
                raise serializers.ValidationError(
                    {
                        "fecha_fin": "La fecha de fin debe ser posterior a la fecha de inicio"
                    }
                )

        # Validar que si el estado es COMPLETADA, debe tener fecha_fin
        if data.get("estado_gestion") == "COMPLETADA" and not data.get("fecha_fin"):
            raise serializers.ValidationError(
                {"fecha_fin": "Una gestión completada debe tener fecha de fin"}
            )

        return data


class GestionListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listado de gestiones
    """

    episodio_id = serializers.UUIDField(source="episodio.id", read_only=True)
    paciente_nombre = serializers.CharField(
        source="episodio.paciente.nombre", read_only=True
    )
    usuario_nombre = serializers.SerializerMethodField()
    tipo_gestion_display = serializers.CharField(
        source="get_tipo_gestion_display", read_only=True
    )
    estado_gestion_display = serializers.CharField(
        source="get_estado_gestion_display", read_only=True
    )

    class Meta:
        model = Gestion
        fields = [
            "id",
            "episodio_id",
            "paciente_nombre",
            "usuario_nombre",
            "tipo_gestion",
            "tipo_gestion_display",
            "estado_gestion",
            "estado_gestion_display",
            "fecha_inicio",
            "fecha_fin",
            "created_at",
        ]

    def get_usuario_nombre(self, obj):
        """
        Retorna el nombre completo del usuario si existe
        """
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return None


class GestionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualización de gestiones
    """

    class Meta:
        model = Gestion
        fields = [
            "usuario",
            "tipo_gestion",
            "estado_gestion",
            "fecha_inicio",
            "fecha_fin",
            "informe",
        ]

    def validate(self, data):
        """
        Validación adicional para actualización
        """
        # Obtener la instancia actual
        instance = self.instance

        # Usar los valores actuales si no se proporcionan nuevos
        fecha_inicio = data.get("fecha_inicio", instance.fecha_inicio)
        fecha_fin = data.get("fecha_fin", instance.fecha_fin)
        estado_gestion = data.get("estado_gestion", instance.estado_gestion)

        # Validar que fecha_fin sea posterior a fecha_inicio si existe
        if fecha_fin and fecha_inicio:
            if fecha_fin < fecha_inicio:
                raise serializers.ValidationError(
                    {
                        "fecha_fin": "La fecha de fin debe ser posterior a la fecha de inicio"
                    }
                )

        # Validar que si el estado es COMPLETADA, debe tener fecha_fin
        if estado_gestion == "COMPLETADA" and not fecha_fin:
            raise serializers.ValidationError(
                {"fecha_fin": "Una gestión completada debe tener fecha de fin"}
            )

        return data
