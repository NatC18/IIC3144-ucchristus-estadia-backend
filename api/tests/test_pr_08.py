from datetime import date

from django.utils import timezone
from rest_framework import status

from api.models import Episodio, Gestion, Paciente
from api.tests.base_test import AuthenticatedAPITestCase


class CrearGestionIntegrationTest(AuthenticatedAPITestCase):
    """PR-08 | HU-16 | Test de Integración: Crear gestión asociada a un episodio"""

    def setUp(self):
        self.authenticate_admin()

        # Crear un paciente y un episodio base
        self.paciente = Paciente.objects.create(
            rut="12.345.678-9",
            nombre="Juan Pérez",
            sexo="M",
            fecha_nacimiento=date(1990, 6, 15),
        )

        self.episodio = Episodio.objects.create(
            paciente=self.paciente,
            episodio_cmbd=1001,
            fecha_ingreso=timezone.now(),
        )

        # Endpoint general para crear gestiones
        self.url = "/api/gestiones/"

    def test_crear_gestion_asociada(self):
        """Debe permitir crear una gestión asociada a un episodio"""
        data = {
            "episodio": str(self.episodio.id),
            "tipo_gestion": "GESTION_CLINICA",
            "estado_gestion": "INICIADA",
            "fecha_inicio": timezone.now().isoformat(),
            "descripcion": "Revisión médica inicial",
        }

        response = self.client.post(self.url, data, format="json")

        # --- Validaciones ---
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(str(response.data["episodio"]), str(self.episodio.id))

        # Verificar persistencia en la base de datos
        gestion = Gestion.objects.get(id=response.data["id"])
        self.assertEqual(gestion.episodio.id, self.episodio.id)
        self.assertEqual(gestion.tipo_gestion, "GESTION_CLINICA")
