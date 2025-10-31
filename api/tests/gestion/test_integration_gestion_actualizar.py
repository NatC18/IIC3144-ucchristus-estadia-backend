from datetime import date

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from api.models import Episodio, Gestion, Paciente
from api.tests.base_test import AuthenticatedAPITestCase


class ActualizarGestionIntegrationTest(AuthenticatedAPITestCase):
    """PR-10 | HU-17 | Test de Integración: Verifica que el gestor pueda cambiar el estado de cada tarea (pendiente, en progreso, resuelta)"""

    def setUp(self):
        self.authenticate_admin()
        self.paciente = Paciente.objects.create(
            rut="12.345.678-9",
            nombre="Juan Pérez",
            sexo="M",
            fecha_nacimiento=date(1985, 6, 10),
        )
        self.episodio = Episodio.objects.create(
            paciente=self.paciente, episodio_cmbd=100, fecha_ingreso=timezone.now()
        )
        self.gestion = Gestion.objects.create(
            episodio=self.episodio,
            usuario=None,
            tipo_gestion="GESTION_CLINICA",
            estado_gestion="INICIADA",
            fecha_inicio=timezone.now(),
        )
        self.url = reverse("gestion-detail", args=[self.gestion.id])

    def test_actualizar_estado_gestion(self):
        data = {"estado_gestion": "EN_PROGRESO"}
        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.gestion.refresh_from_db()
        self.assertEqual(self.gestion.estado_gestion, "EN_PROGRESO")
