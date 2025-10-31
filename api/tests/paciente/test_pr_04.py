from datetime import date, datetime, timezone

from api.models import Episodio, Paciente
from api.tests.base_test import AuthenticatedAPITestCase


class VisualizarFichaPacienteIntegrationTest(AuthenticatedAPITestCase):
    """PR-04 | HU-05 | Test de integración: Visualización de ficha del paciente"""

    def setUp(self):
        self.authenticate_admin()

        # Crear paciente
        self.paciente = Paciente.objects.create(
            rut="12.345.678-5",
            nombre="Juan Pérez",
            sexo="M",
            fecha_nacimiento=date(1985, 5, 10),
        )

        # Crear episodios con fecha_ingreso requerida
        Episodio.objects.create(
            paciente=self.paciente,
            episodio_cmbd=11,
            fecha_ingreso=datetime.now(timezone.utc),
        )
        Episodio.objects.create(
            paciente=self.paciente,
            episodio_cmbd=22,
            fecha_ingreso=datetime.now(timezone.utc),
        )

    def test_visualizar_ficha_paciente(self):
        """Debe devolver todos los episodios asociados a un paciente"""
        url = f"/api/pacientes/{self.paciente.id}/episodios/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

        # Verifica que los episodios correspondan al paciente
        for episodio in response.data:
            self.assertIn("episodio_cmbd", episodio)
