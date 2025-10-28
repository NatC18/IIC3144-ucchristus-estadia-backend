from datetime import date

from django.utils import timezone
from rest_framework import status

from api.models import Episodio, Paciente
from api.tests.base_test import AuthenticatedAPITestCase


class EstadoGlobalIntegrationTest(AuthenticatedAPITestCase):
    """PR-23 | HU-09 | Test de Integración: Consultar estado global de pacientes"""

    def setUp(self):
        self.authenticate_admin()

        # Crear pacientes y episodios simulados
        self.paciente1 = Paciente.objects.create(
            rut="11.111.111-1",
            nombre="María López",
            sexo="F",
            fecha_nacimiento=date(1990, 5, 10),
        )

        self.paciente2 = Paciente.objects.create(
            rut="22.222.222-2",
            nombre="Carlos Díaz",
            sexo="M",
            fecha_nacimiento=date(1982, 11, 23),
        )

        # Crear episodios hospitalarios
        Episodio.objects.create(
            paciente=self.paciente1,
            episodio_cmbd=101,
            fecha_ingreso=timezone.now(),
        )
        Episodio.objects.create(
            paciente=self.paciente2,
            episodio_cmbd=102,
            fecha_ingreso=timezone.now(),
        )

        # Endpoint global (ajústalo según tu ruta real)
        self.url = "/api/episodios/"  # ejemplo más común

    def test_consultar_estado_global(self):
        """Debe permitir al admin obtener la lista global de episodios hospitalizados"""
        response = self.client.get(self.url)

        # --- Validaciones ---
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verifica formato: puede ser lista o dict con 'results'
        if isinstance(response.data, dict) and "results" in response.data:
            episodios = response.data["results"]
        else:
            episodios = response.data

        self.assertIsInstance(episodios, list)
        self.assertGreaterEqual(len(episodios), 2)

        # Verifica estructura básica de los episodios
        for episodio in episodios:
            self.assertIn("paciente", episodio)
            self.assertIn("episodio_cmbd", episodio)
            self.assertIn("fecha_ingreso", episodio)
