from datetime import date

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from api.models import Episodio, Paciente, User
from api.models.gestion import Gestion
from api.serializers.gestion import GestionCreateSerializer


class GestionCreateSerializerTest(TestCase):
    """Tests unitarios para creación de gestiones (PR-11)"""

    def setUp(self):
        # Crear un paciente de prueba válido según el modelo real
        self.paciente = Paciente.objects.create(
            rut="12.345.678-9",
            nombre="Juan Pérez",
            sexo="M",
            fecha_nacimiento=date(1980, 5, 20),
            prevision_1="FONASA",
        )

        # Crear un usuario gestor
        self.usuario = User.objects.create(
            nombre="Felipe", apellido="Abarca", email="gestor@test.cl"
        )

        # Crear un episodio asociado al paciente
        self.episodio = Episodio.objects.create(
            paciente=self.paciente, episodio_cmbd=1, fecha_ingreso=timezone.now()
        )

        # Fechas de prueba
        self.fecha_inicio = timezone.now()
        self.fecha_fin_correcta = self.fecha_inicio + timezone.timedelta(days=2)
        self.fecha_fin_invalida = self.fecha_inicio - timezone.timedelta(days=1)

    def test_creacion_gestion_valida(self):
        data = {
            "episodio": self.episodio.id,
            "usuario": self.usuario.id,
            "tipo_gestion": "TRASLADO",
            "estado_gestion": "INICIADA",
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin_correcta,
            "informe": "Gestión inicial de traslado creada correctamente",
        }

        serializer = GestionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        gestion = serializer.save()

        self.assertIsInstance(gestion, Gestion)
        self.assertEqual(gestion.tipo_gestion, "TRASLADO")
        self.assertEqual(gestion.estado_gestion, "INICIADA")
        self.assertEqual(gestion.usuario, self.usuario)
        self.assertEqual(gestion.episodio, self.episodio)
