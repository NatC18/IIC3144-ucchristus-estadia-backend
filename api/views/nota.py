"""
Views para el modelo Nota
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from api.models import Nota
from api.serializers import (
    NotaCreateSerializer,
    NotaListSerializer,
    NotaSerializer,
    NotaUpdateSerializer,
)


class NotaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de notas

    Operaciones disponibles:
    - GET /api/notas/ - Listar notas
    - POST /api/notas/ - Crear nota
    - GET /api/notas/{id}/ - Obtener nota específica
    - PUT /api/notas/{id}/ - Actualizar nota completa
    - PATCH /api/notas/{id}/ - Actualizar nota parcial
    - DELETE /api/notas/{id}/ - Eliminar nota
    """

    queryset = Nota.objects.select_related("gestion", "usuario").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción
        """
        if self.action == "create":
            return NotaCreateSerializer
        elif self.action == "list":
            return NotaListSerializer
        elif self.action in ["update", "partial_update"]:
            return NotaUpdateSerializer
        return NotaSerializer
