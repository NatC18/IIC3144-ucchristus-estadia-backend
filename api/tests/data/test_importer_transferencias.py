from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from api.models import Paciente, Episodio, Gestion, Transferencia
from api.management.modules.db_importer import DatabaseImporter

class DatabaseImporterTransferenciaTest(TestCase):
    """Tests de importación de transferencias usando DatabaseImporter"""

    def setUp(self):
        # Inicializar importador
        self.importer = DatabaseImporter()

        # Crear paciente y episodio existente
        self.paciente = Paciente.objects.create(
            rut="12.345.678-9",
            nombre="Paciente Test",
            sexo="F",
            fecha_nacimiento=datetime(1990, 1, 1),
        )

        self.episodio = Episodio.objects.create(
            episodio_cmbd=1,
            paciente=self.paciente,
            fecha_ingreso=timezone.now() - timedelta(days=5),
        )

    def test_crea_transferencia_nueva(self):
        """Debe crear una nueva transferencia y gestión asociada"""
        transferencias_data = [
            {
                "episodio_cmbd": self.episodio.episodio_cmbd,
                "estado": "PENDIENTE",
                "tipo_traslado": "INTERNO",
                "motivo_traslado": "Cambio de sala",
                "centro_destinatario": "Unidad A",
                "fecha_solicitud": timezone.now(),
            }
        ]

        self.importer._import_transferencias(transferencias_data)

        gestion = Gestion.objects.get(episodio=self.episodio, tipo_gestion="TRANSFERENCIA")
        transferencia = Transferencia.objects.get(gestion=gestion)

        self.assertEqual(transferencia.estado, "PENDIENTE")
        self.assertEqual(transferencia.tipo_traslado, "INTERNO")
        self.assertEqual(transferencia.motivo_traslado, "Cambio de sala")
        self.assertEqual(transferencia.centro_destinatario, "Unidad A")
        self.assertEqual(self.importer.results["transferencias"]["created"], 1)
        self.assertEqual(self.importer.results["transferencias"]["updated"], 0)
        self.assertEqual(self.importer.results["transferencias"]["errors"], 0)

    def test_actualiza_transferencia_existente(self):
        """Debe actualizar una transferencia existente"""
        # Crear gestión y transferencia inicial
        gestion = Gestion.objects.create(
            episodio=self.episodio,
            tipo_gestion="TRANSFERENCIA",
            estado_gestion="INICIADA",
            fecha_inicio=timezone.now()
        )
        transferencia = Transferencia.objects.create(
            gestion=gestion,
            estado="PENDIENTE",
            tipo_traslado="INTERNO",
            motivo_traslado="Cambio de sala",
            centro_destinatario="Unidad A",
        )

        # Datos para actualizar
        transferencias_data = [
            {
                "episodio_cmbd": self.episodio.episodio_cmbd,
                "estado": "COMPLETADO",
                "motivo_traslado": "Traslado finalizado",
            }
        ]

        self.importer._import_transferencias(transferencias_data)

        transferencia.refresh_from_db()
        self.assertEqual(transferencia.estado, "COMPLETADO")
        self.assertEqual(transferencia.motivo_traslado, "Traslado finalizado")
        self.assertEqual(self.importer.results["transferencias"]["created"], 0)
        self.assertEqual(self.importer.results["transferencias"]["updated"], 1)
        self.assertEqual(self.importer.results["transferencias"]["errors"], 0)

    def test_error_sin_episodio(self):
        """Debe registrar error si no se encuentra el episodio"""
        transferencias_data = [
            {
                "episodio_cmbd": 999,  # Episodio inexistente
                "estado": "PENDIENTE",
            }
        ]

        self.importer._import_transferencias(transferencias_data)

        self.assertEqual(self.importer.results["transferencias"]["errors"], 1)
        self.assertIn("No se encontró episodio 999 para transferencia", self.importer.error_details)
