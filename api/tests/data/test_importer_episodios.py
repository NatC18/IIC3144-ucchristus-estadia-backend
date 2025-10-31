from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from api.management.modules.db_importer import DatabaseImporter
from api.models import Cama, Episodio, Paciente


class DatabaseImporterEpisodioTest(TestCase):
    """Tests de importación de episodios usando DatabaseImporter"""

    def setUp(self):
        # Inicializar importador
        self.importer = DatabaseImporter()

        # Crear paciente y cama existentes
        self.paciente = Paciente.objects.create(
            rut="12.345.678-9",
            nombre="Paciente Test",
            sexo="F",
            fecha_nacimiento=datetime(1990, 1, 1),
            prevision_1="FONASA",
        )

        self.cama = Cama.objects.create(
            codigo_cama="CAMA-001",
            habitacion="HAB-101",
        )

        # Episodio existente
        self.existing_episodio = Episodio.objects.create(
            episodio_cmbd=1,
            paciente=self.paciente,
            cama=self.cama,
            fecha_ingreso=timezone.now() - timedelta(days=5),
        )

    def test_crea_episodio_nuevo(self):
        """Debe crear un episodio nuevo asociado a paciente y cama"""

        otra_cama = Cama.objects.create(codigo_cama="CAMA-002", habitacion="HAB-102")

        episodios_data = [
            {
                "episodio_cmbd": 2,
                "rut_paciente": self.paciente.rut,
                "codigo_cama": otra_cama.codigo_cama,
                "fecha_ingreso": timezone.now(),
                "tipo_actividad": "Hospitalización",
            }
        ]

        self.importer._import_episodios(episodios_data)

        episodio = Episodio.objects.get(episodio_cmbd=2)
        self.assertEqual(episodio.paciente, self.paciente)
        self.assertEqual(episodio.cama, otra_cama)
        self.assertEqual(self.importer.results["episodios"]["created"], 1)
        self.assertEqual(self.importer.results["episodios"]["updated"], 0)
        self.assertEqual(self.importer.results["episodios"]["errors"], 0)

    def test_actualiza_episodio_existente(self):
        """Debe actualizar el episodio existente con nueva fecha de egreso"""
        nueva_fecha_egreso = timezone.now()
        episodios_data = [
            {
                "episodio_cmbd": self.existing_episodio.episodio_cmbd,
                "fecha_egreso": nueva_fecha_egreso,
            }
        ]

        self.importer._import_episodios(episodios_data)

        episodio = Episodio.objects.get(
            episodio_cmbd=self.existing_episodio.episodio_cmbd
        )
        self.assertEqual(episodio.fecha_egreso, nueva_fecha_egreso)
        self.assertEqual(self.importer.results["episodios"]["created"], 0)
        self.assertEqual(self.importer.results["episodios"]["updated"], 1)
        self.assertEqual(self.importer.results["episodios"]["errors"], 0)

    def test_error_sin_paciente(self):
        """Debe registrar error si no se encuentra paciente para el episodio"""
        episodios_data = [
            {
                "episodio_cmbd": 3,
                "rut_paciente": "99.999.999-9",  # Paciente inexistente
                "codigo_cama": self.cama.codigo_cama,
                "fecha_ingreso": timezone.now(),
            }
        ]

        self.importer._import_episodios(episodios_data)

        self.assertEqual(self.importer.results["episodios"]["errors"], 1)
        self.assertIn(
            "No se encontró paciente para episodio 3", self.importer.error_details
        )
