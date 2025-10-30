from django.test import TestCase

from api.management.modules.db_importer import DatabaseImporter
from api.models import Cama


class DatabaseImporterCamaTest(TestCase):
    """Tests de importación de camas usando DatabaseImporter"""

    def setUp(self):
        # Inicializar importador
        self.importer = DatabaseImporter()

        # Cama existente
        self.existing_cama = Cama.objects.create(
            codigo_cama="CAMA-001",
            habitacion="HAB-101",
        )

    def test_crea_cama_nueva(self):
        """Debe crear una cama que no existe"""
        camas_data = [
            {
                "codigo_cama": "CAMA-002",
                "habitacion": "HAB-102",
            }
        ]

        self.importer._import_camas(camas_data)

        cama = Cama.objects.get(codigo_cama="CAMA-002")
        self.assertEqual(cama.habitacion, "HAB-102")

        self.assertEqual(self.importer.results["camas"]["created"], 1)
        self.assertEqual(self.importer.results["camas"]["updated"], 0)
        self.assertEqual(self.importer.results["camas"]["errors"], 0)

    def test_actualiza_cama_existente(self):
        """Debe actualizar la habitación de una cama existente"""
        camas_data = [
            {
                "codigo_cama": self.existing_cama.codigo_cama,
                "habitacion": "HAB-201",  # Nueva habitación
            }
        ]

        self.importer._import_camas(camas_data)

        cama = Cama.objects.get(codigo_cama=self.existing_cama.codigo_cama)
        self.assertEqual(cama.habitacion, "HAB-201")

        self.assertEqual(self.importer.results["camas"]["created"], 0)
        self.assertEqual(self.importer.results["camas"]["updated"], 1)
        self.assertEqual(self.importer.results["camas"]["errors"], 0)

    def test_error_sin_codigo(self):
        """Debe registrar error si no se entrega código de cama"""
        camas_data = [
            {
                "habitacion": "HAB-999",
            }
        ]

        self.importer._import_camas(camas_data)

        self.assertEqual(self.importer.results["camas"]["errors"], 1)
        self.assertIn("Cama sin código", self.importer.error_details)
