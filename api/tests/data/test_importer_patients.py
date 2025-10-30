from datetime import date
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.management.modules.db_importer import DatabaseImporter
from api.models import Paciente


class DatabaseImporterPacienteTest(TestCase):
    """Tests de importación de pacientes usando DatabaseImporter"""

    def setUp(self):
        # Inicializamos el importador
        self.importer = DatabaseImporter()

        # Paciente existente
        self.existing_paciente = Paciente.objects.create(
            rut="12.345.678-9",
            nombre="Juan Pérez",
            sexo="M",
            fecha_nacimiento=date(1990, 5, 10),
            prevision_1="FONASA",
        )

    def test_crea_paciente_nuevo(self):
        """Debe crear un paciente que no existe en la base de datos"""
        paciente_data = [
            {
                "rut": "98.765.432-1",
                "nombre": "María Gómez",
                "sexo": "F",
                "fecha_nacimiento": date(1985, 4, 15),
                "prevision_1": "ISAPRE",
                "prevision_2": None,
                "convenio": None,
                "score_social": None,
                "episodio_cmbd": 1,
            }
        ]

        result = self.importer._import_pacientes(paciente_data)

        # Debe haberse creado un paciente
        paciente = Paciente.objects.get(rut="98.765.432-1")
        self.assertEqual(paciente.nombre, "María Gómez")
        self.assertEqual(paciente.sexo, "F")
        self.assertEqual(paciente.prevision_1, "ISAPRE")

        # Revisar contador interno del importador
        self.assertEqual(self.importer.results["pacientes"]["created"], 1)
        self.assertEqual(self.importer.results["pacientes"]["updated"], 0)
        self.assertEqual(self.importer.results["pacientes"]["errors"], 0)

    def test_actualiza_paciente_existente(self):
        """Debe actualizar un paciente existente si hay nueva información"""
        paciente_data = [
            {
                "rut": self.existing_paciente.rut,
                "nombre": "Juan Pérez Actualizado",
                "sexo": "M",
                "fecha_nacimiento": date(1990, 5, 10),
                "prevision_1": "FONASA",
                "prevision_2": "ADICIONAL",
                "convenio": "Convenio X",
                "score_social": 5,
                "episodio_cmbd": 2,
            }
        ]

        self.importer._import_pacientes(paciente_data)

        paciente = Paciente.objects.get(rut=self.existing_paciente.rut)
        self.assertEqual(paciente.nombre, "Juan Pérez Actualizado")
        self.assertEqual(paciente.prevision_2, "ADICIONAL")
        self.assertEqual(paciente.convenio, "Convenio X")
        self.assertEqual(paciente.score_social, 5)

        self.assertEqual(self.importer.results["pacientes"]["created"], 0)
        self.assertEqual(self.importer.results["pacientes"]["updated"], 1)
        self.assertEqual(self.importer.results["pacientes"]["errors"], 0)

    def test_error_sin_rut(self):
        """Debe registrar error si no se entrega RUT"""
        paciente_data = [
            {
                "nombre": "Paciente Sin RUT",
                "sexo": "F",
                "fecha_nacimiento": date(2000, 1, 1),
                "prevision_1": "FONASA",
                "episodio_cmbd": 3,
            }
        ]

        self.importer._import_pacientes(paciente_data)

        # Debe aumentar contador de errores
        self.assertEqual(self.importer.results["pacientes"]["errors"], 1)
        self.assertIn("Paciente sin RUT", self.importer.error_details[0])


class DatabaseImporterPacienteErrorTest(TestCase):
    """Tests de errores en importación de pacientes"""

    def setUp(self):
        self.importer = DatabaseImporter()

    def test_validation_error(self):
        """Debe registrar un error si Django lanza ValidationError"""
        paciente_data = [
            {
                "rut": "12.345.678-9",
                "nombre": "Paciente Inválido",
                "sexo": "F",
                "fecha_nacimiento": date(2000, 1, 1),
                "prevision_1": "FONASA",
                "episodio_cmbd": 1,
            }
        ]

        # Forzamos que Paciente.objects.get_or_create lance ValidationError
        with patch("api.models.Paciente.objects.get_or_create") as mock_get_or_create:
            mock_get_or_create.side_effect = ValidationError("Validación forzada")
            self.importer._import_pacientes(paciente_data)

        self.assertEqual(self.importer.results["pacientes"]["errors"], 1)
        self.assertIn("Error validación paciente", self.importer.error_details[0])

    def test_generic_exception(self):
        """Debe registrar un error si ocurre un Exception genérico"""
        paciente_data = [
            {
                "rut": "12.345.678-9",
                "nombre": "Paciente Excepción",
                "sexo": "F",
                "fecha_nacimiento": date(2000, 1, 1),
                "prevision_1": "FONASA",
                "episodio_cmbd": 1,
            }
        ]

        # Forzamos un error genérico
        with patch("api.models.Paciente.objects.get_or_create") as mock_get_or_create:
            mock_get_or_create.side_effect = Exception("Error genérico forzado")
            self.importer._import_pacientes(paciente_data)

        self.assertEqual(self.importer.results["pacientes"]["errors"], 1)
        self.assertIn("Error procesando paciente", self.importer.error_details[0])
