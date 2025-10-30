import pytest
from unittest.mock import patch, MagicMock
from api.management.modules.db_importer import DatabaseImporter

@pytest.fixture
def sample_paciente_data():
    return [
        {
            "rut": "12345678-9",
            "nombre": "Juan Pérez",
            "sexo": "M",
            "fecha_nacimiento": "1990-01-01",
            "prevision_1": "ISAPRE",
            "prevision_2": "OTRO",
            "convenio": "Convenio A",
            "score_social": 5,
            "episodio_cmbd": 1,
        }
    ]

def test_import_pacientes_creacion(sample_paciente_data):
    importer = DatabaseImporter()

    
    with patch("api.models.Paciente.objects.get_or_create") as mock_get_or_create:
        # Simular que el paciente no existe (created=True)
        mock_paciente_instance = MagicMock()
        mock_get_or_create.return_value = (mock_paciente_instance, True)

        importer._import_pacientes(sample_paciente_data)

        # Verificar que get_or_create fue llamado con el RUT correcto
        mock_get_or_create.assert_called_with(
            rut="12345678-9",
            defaults={
                "nombre": "Juan Pérez",
                "sexo": "M",
                "fecha_nacimiento": "1990-01-01",
                "prevision_1": "ISAPRE",
                "prevision_2": "OTRO",
                "convenio": "Convenio A",
                "score_social": 5,
            },
        )

        # Como es creación, save no debería llamarse
        assert not mock_paciente_instance.save.called

        # Verificar resultados internos
        assert importer.results["pacientes"]["created"] == 1
        assert importer.results["pacientes"]["updated"] == 0
        assert importer.results["pacientes"]["errors"] == 0

def test_import_pacientes_actualizacion(sample_paciente_data):
    importer = DatabaseImporter()

    # Mock de get_or_create simulando que el paciente ya existe
    with patch("api.models.Paciente.objects.get_or_create") as mock_get_or_create:
        mock_paciente_instance = MagicMock()
        mock_paciente_instance.nombre = "Juan Pérez"
        mock_paciente_instance.sexo = "O"
        mock_paciente_instance.fecha_nacimiento = None
        mock_paciente_instance.prevision_1 = "OTRO"
        mock_paciente_instance.prevision_2 = None
        mock_paciente_instance.convenio = None
        mock_paciente_instance.score_social = None

        mock_get_or_create.return_value = (mock_paciente_instance, False)

        importer._import_pacientes(sample_paciente_data)

        # Verificar que save se llamó porque hubo actualización
        assert mock_paciente_instance.save.called

        # Verificar resultados internos
        assert importer.results["pacientes"]["created"] == 0
        assert importer.results["pacientes"]["updated"] == 1
        assert importer.results["pacientes"]["errors"] == 0
