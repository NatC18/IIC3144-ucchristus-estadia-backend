from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from api.management.modules.db_importer import DatabaseImporter
from api.models import Cama, Episodio, Gestion, Paciente

User = get_user_model()

class DatabaseImporterGestionTest(TestCase):
    """Tests de importación de gestiones usando DatabaseImporter"""

    def setUp(self):
        # Inicializar importador
        self.importer = DatabaseImporter()

        # Crear paciente, cama y episodio existentes
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

        self.episodio = Episodio.objects.create(
            episodio_cmbd=1,
            paciente=self.paciente,
            cama=self.cama,
            fecha_ingreso=timezone.now() - timedelta(days=5),
        )

        # Crear usuario de prueba
        self.usuario = User.objects.create_user(
            email="usuario@test.com", password="password123"
        )

    def test_crea_gestion_nueva(self):
        """Debe crear una gestión nueva asociada a un episodio existente"""
        gestiones_data = [
            {
                "episodio_cmbd": self.episodio.episodio_cmbd,
                "tipo_gestion": "CONTROL",
                "estado_gestion": "INICIADA",
                "fecha_inicio": timezone.now(),
                "fecha_fin": None,
                "usuario_email": self.usuario.email,
                "informe": "Informe de prueba",
            }
        ]

        self.importer._import_gestiones(gestiones_data)

        gestion = Gestion.objects.get(episodio=self.episodio)
        self.assertEqual(gestion.tipo_gestion, "CONTROL")
        self.assertEqual(gestion.estado_gestion, "INICIADA")
        self.assertEqual(gestion.informe, "Informe de prueba")
        self.assertEqual(gestion.usuario, self.usuario)

        self.assertEqual(self.importer.results["gestiones"]["created"], 1)
        self.assertEqual(self.importer.results["gestiones"]["errors"], 0)

    def test_error_gestion_sin_episodio(self):
        """Debe registrar error si no se encuentra episodio para la gestión"""
        gestiones_data = [
            {
                "episodio_cmbd": 9999,  # Episodio inexistente
                "tipo_gestion": "CONTROL",
                "estado_gestion": "INICIADA",
            }
        ]

        self.importer._import_gestiones(gestiones_data)

        self.assertEqual(self.importer.results["gestiones"]["created"], 0)
        self.assertEqual(self.importer.results["gestiones"]["errors"], 1)
        self.assertIn(
            "No se encontró episodio 9999 para gestión", self.importer.error_details
        )

    def test_crea_gestion_sin_usuario(self):
        """Debe crear gestión aunque no se especifique usuario"""
        gestiones_data = [
            {
                "episodio_cmbd": self.episodio.episodio_cmbd,
                "tipo_gestion": "ADMINISTRATIVA",
                "estado_gestion": "INICIADA",
                "fecha_inicio": timezone.now(),
            }
        ]

        self.importer._import_gestiones(gestiones_data)

        gestion = Gestion.objects.get(
            episodio=self.episodio, tipo_gestion="ADMINISTRATIVA"
        )
        self.assertIsNone(gestion.usuario)
        self.assertEqual(self.importer.results["gestiones"]["created"], 1)
        self.assertEqual(self.importer.results["gestiones"]["errors"], 0)