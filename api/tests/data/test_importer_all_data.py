from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from api.management.modules.db_importer import DatabaseImporter
from api.models import Cama, Episodio, Gestion, Paciente


class DatabaseImporterAllDataTest(TestCase):
    """Tests de importación completa de datos con DatabaseImporter"""

    def setUp(self):
        self.importer = DatabaseImporter()

        # Datos de prueba para cada entidad
        self.pacientes_data = [
            {
                "rut": "12.345.678-9",
                "nombre": "Paciente Test",
                "sexo": "F",
                "fecha_nacimiento": datetime(1990, 1, 1),
                "prevision_1": "FONASA",
            }
        ]

        self.camas_data = [
            {
                "codigo_cama": "CAMA-001",
                "habitacion": "HAB-101",
            }
        ]

        self.episodios_data = [
            {
                "episodio_cmbd": 1,
                "rut_paciente": "12.345.678-9",
                "codigo_cama": "CAMA-001",
                "fecha_ingreso": timezone.now(),
                "tipo_actividad": "Hospitalización",
            }
        ]

        self.gestiones_data = [
            {
                "tipo_gestion": "ALTA",
                "fecha_inicio": timezone.now(),
                "episodio_cmbd": 1,
            }
        ]

        self.transferencias_data = [
            {
                "episodio_cmbd": 1,
                "origen": "UCI",
                "destino": "Sala Común",
                "fecha_transferencia": timezone.now(),
            }
        ]

    def test_importa_todos_los_datos(self):
        """Debe importar correctamente pacientes, camas, episodios, gestiones y transferencias"""

        mapped_data = {
            "pacientes": self.pacientes_data,
            "camas": self.camas_data,
            "episodios": self.episodios_data,
            "gestiones": self.gestiones_data,
            "transferencias": self.transferencias_data,
        }

        result = self.importer.import_all_data(mapped_data)

        # Validar que todo fue creado correctamente
        self.assertEqual(Paciente.objects.count(), 1)
        self.assertEqual(Cama.objects.count(), 1)
        self.assertEqual(Episodio.objects.count(), 1)
        self.assertEqual(Gestion.objects.count(), 1)

        # Validar resumen de resultados
        episodios_result = self.importer.results.get("episodios", {})
        self.assertIn("created", episodios_result)
        self.assertEqual(episodios_result["errors"], 0)

        # Validar estructura del resultado global
        self.assertIsInstance(result, dict)
        self.assertIn("pacientes", self.importer.results)
        self.assertIn("gestiones", self.importer.results)

    def test_no_falla_con_datos_incompletos(self):
        """Debe manejar correctamente si falta alguna sección en mapped_data"""
        mapped_data = {
            "pacientes": self.pacientes_data,
            "episodios": [],  # Sin camas ni gestiones
        }

        result = self.importer.import_all_data(mapped_data)

        # Debe crear al menos el paciente
        self.assertEqual(Paciente.objects.count(), 1)
        self.assertEqual(Episodio.objects.count(), 0)
        self.assertIsInstance(result, dict)
        self.assertEqual(self.importer.results["pacientes"]["created"], 1)
