"""
Serializers para el modelo Gestion
"""

from datetime import datetime

from rest_framework import serializers

from api.models import Gestion

from .nota import NotaListSerializer


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
    estado_traslado_display = serializers.SerializerMethodField()
    tipo_traslado_display = serializers.SerializerMethodField()
    tipo_solicitud_traslado_display = serializers.SerializerMethodField()
    nivel_atencion_traslado_display = serializers.SerializerMethodField()
    # Custom fields for related data
    episodio_cmbd = serializers.SerializerMethodField()
    paciente_nombre = serializers.SerializerMethodField()
    paciente_id = serializers.SerializerMethodField()
    # Notas relacionadas
    notas = NotaListSerializer(many=True, read_only=True)

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
            "episodio_cmbd",
            "paciente_nombre",
            "paciente_id",
            # Campos de traslado
            "estado_traslado",
            "estado_traslado_display",
            "tipo_traslado",
            "tipo_traslado_display",
            "motivo_traslado",
            "centro_destinatario",
            "tipo_solicitud_traslado",
            "tipo_solicitud_traslado_display",
            "nivel_atencion_traslado",
            "nivel_atencion_traslado_display",
            "motivo_rechazo_traslado",
            "motivo_cancelacion_traslado",
            "fecha_finalizacion_traslado",
            # Notas
            "notas",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_usuario_nombre(self, obj):
        """
        Retorna el nombre completo del usuario si existe
        """
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return None

    def get_paciente_nombre(self, obj):
        """
        Retorna el nombre del paciente asociado al episodio
        """
        if obj.episodio and obj.episodio.paciente:
            return obj.episodio.paciente.nombre
        return None

    def get_episodio_cmbd(self, obj):
        """
        Retorna el episodio_cmbd del episodio asociado
        """
        if obj.episodio:
            return obj.episodio.episodio_cmbd
        return None

    def get_paciente_id(self, obj):
        """
        Retorna el ID del paciente asociado al episodio
        """
        if obj.episodio and obj.episodio.paciente:
            return str(obj.episodio.paciente.id)
        return None

    def get_estado_traslado_display(self, obj):
        """
        Retorna el display del estado de traslado solo si es tipo TRASLADO
        """
        if obj.tipo_gestion == "TRASLADO" and obj.estado_traslado:
            return obj.get_estado_traslado_display()
        return None

    def get_tipo_traslado_display(self, obj):
        """
        Retorna el display del tipo de traslado solo si es tipo TRASLADO
        """
        if obj.tipo_gestion == "TRASLADO" and obj.tipo_traslado:
            return obj.get_tipo_traslado_display()
        return None

    def get_tipo_solicitud_traslado_display(self, obj):
        """
        Retorna el display del tipo de solicitud solo si es tipo TRASLADO
        """
        if obj.tipo_gestion == "TRASLADO" and obj.tipo_solicitud_traslado:
            return obj.get_tipo_solicitud_traslado_display()
        return None

    def get_nivel_atencion_traslado_display(self, obj):
        """
        Retorna el display del nivel de atención solo si es tipo TRASLADO
        """
        if obj.tipo_gestion == "TRASLADO" and obj.nivel_atencion_traslado:
            return obj.get_nivel_atencion_traslado_display()
        return None

    def to_representation(self, instance):
        """
        Personaliza la representación para ocultar campos de traslado si no es tipo TRASLADO
        """
        data = super().to_representation(instance)

        # Si no es tipo TRASLADO, remover los campos de traslado
        if instance.tipo_gestion != "TRASLADO":
            traslado_fields = [
                "estado_traslado",
                "estado_traslado_display",
                "tipo_traslado",
                "tipo_traslado_display",
                "motivo_traslado",
                "centro_destinatario",
                "tipo_solicitud_traslado",
                "tipo_solicitud_traslado_display",
                "nivel_atencion_traslado",
                "nivel_atencion_traslado_display",
                "motivo_rechazo_traslado",
                "motivo_cancelacion_traslado",
            ]
            for field in traslado_fields:
                data.pop(field, None)

        return data


class GestionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para creación de gestiones
    """

    class Meta:
        model = Gestion
        fields = [
            "id",
            "episodio",
            "usuario",
            "tipo_gestion",
            "estado_gestion",
            "fecha_inicio",
            "fecha_fin",
            "informe",
            # Campos de traslado (solo se permiten si tipo_gestion es TRASLADO)
            "estado_traslado",
            "tipo_traslado",
            "motivo_traslado",
            "centro_destinatario",
            "tipo_solicitud_traslado",
            "nivel_atencion_traslado",
            "motivo_rechazo_traslado",
            "motivo_cancelacion_traslado",
            "fecha_finalizacion_traslado",
        ]
        read_only_fields = ["id"]

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

        # Validar campos de traslado si tipo_gestion es TRASLADO
        tipo_gestion = data.get("tipo_gestion")
        if tipo_gestion == "TRASLADO":
            # Al menos algunos campos de traslado deberían ser proporcionados
            traslado_fields = [
                data.get("estado_traslado"),
                data.get("tipo_traslado"),
                data.get("motivo_traslado"),
            ]
            if not any(traslado_fields):
                raise serializers.ValidationError(
                    {
                        "traslado_fields": "Para gestiones de tipo TRASLADO, debe proporcionar al menos el estado, tipo o motivo del traslado"
                    }
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
    estado_traslado_display = serializers.SerializerMethodField()
    tipo_traslado_display = serializers.SerializerMethodField()
    episodio_cmbd = serializers.SerializerMethodField()

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
            "episodio_cmbd",
            # Campos de traslado
            "estado_traslado",
            "estado_traslado_display",
            "tipo_traslado",
            "tipo_traslado_display",
        ]

    def get_usuario_nombre(self, obj):
        """
        Retorna el nombre completo del usuario si existe
        """
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return None

    def get_estado_traslado_display(self, obj):
        """
        Retorna el display del estado de traslado solo si es tipo TRASLADO
        """
        if obj.tipo_gestion == "TRASLADO" and obj.estado_traslado:
            return obj.get_estado_traslado_display()
        return None

    def get_tipo_traslado_display(self, obj):
        """
        Retorna el display del tipo de traslado solo si es tipo TRASLADO
        """
        if obj.tipo_gestion == "TRASLADO" and obj.tipo_traslado:
            return obj.get_tipo_traslado_display()
        return None

    def get_episodio_cmbd(self, obj):
        """
        Retorna el episodio_cmbd del episodio asociado
        """
        if obj.episodio:
            return obj.episodio.episodio_cmbd
        return None

    def to_representation(self, instance):
        """
        Personaliza la representación para ocultar campos de traslado si no es tipo TRASLADO
        """
        data = super().to_representation(instance)

        # Si no es tipo TRASLADO, remover los campos de traslado
        if instance.tipo_gestion != "TRASLADO":
            data.pop("estado_traslado", None)
            data.pop("estado_traslado_display", None)
            data.pop("tipo_traslado", None)
            data.pop("tipo_traslado_display", None)

        return data


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
            # Campos de traslado
            "estado_traslado",
            "tipo_traslado",
            "motivo_traslado",
            "centro_destinatario",
            "tipo_solicitud_traslado",
            "nivel_atencion_traslado",
            "motivo_rechazo_traslado",
            "motivo_cancelacion_traslado",
            "fecha_finalizacion_traslado",
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

    def update(self, instance, validated_data):
        """
        Actualizar instancia con lógica para fecha_finalizacion_traslado
        """
        # Estados finales del traslado
        FINAL_TRASLADO_STATES = ["CANCELADO", "COMPLETADO", "RECHAZADO"]

        # Obtener el nuevo estado_traslado si se proporciona
        nuevo_estado_traslado = validated_data.get(
            "estado_traslado", instance.estado_traslado
        )

        # Si el estado_traslado se cambia a un estado final y no tiene fecha_finalizacion_traslado
        if nuevo_estado_traslado in FINAL_TRASLADO_STATES:
            # Si no se proporciona fecha_finalizacion_traslado, se establece a ahora
            if not validated_data.get("fecha_finalizacion_traslado"):
                validated_data["fecha_finalizacion_traslado"] = datetime.now()

        # Si el estado_traslado se cambia a un estado no final, limpiar fecha_finalizacion_traslado
        elif (
            nuevo_estado_traslado not in FINAL_TRASLADO_STATES and nuevo_estado_traslado
        ):
            validated_data["fecha_finalizacion_traslado"] = None

        return super().update(instance, validated_data)
