import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from api.management.modules.db_importer import DatabaseImporter

@pytest.fixture
def sample_episodio_data():
    return [
        {
            "episodio_cmbd": 1,
            "rut_paciente": "12345678-9",
            "codigo_cama": "CAMA-001",
            "habitacion": "101A",
            "fecha_ingreso": datetime(2025, 10, 29, 10, 0),
            "fecha_egreso": datetime(2025, 10, 30, 12, 0),
            "tipo_actividad": "Hospitalización",
            "especialidad": "Cardiología",
        }
    ]

def test_import_episodios_creacion(sample_episodio_data):
    importer = DatabaseImporter()

    # Mock de pacientes
    mock_paciente = MagicMock()
    importer.episodio_to_paciente = {1: mock_paciente}

    # Mock de camas
    mock_cama = MagicMock()
    with patch("api.management.modules.db_importer.DatabaseImporter._find_cama", return_value=mock_cama):
        # Mock de Episodio.objects.get_or_create
        with patch("api.models.Episodio.objects.get_or_create") as mock_get_or_create:
            mock_episodio_instance = MagicMock()
            mock_get_or_create.return_value = (mock_episodio_instance, True)  # True = creado

            importer._import_episodios(sample_episodio_data)

            # Comprobar que get_or_create se llamó con los valores correctos
            mock_get_or_create.assert_called_once_with(
                episodio_cmbd=1,
                defaults={
                    "paciente": mock_paciente,
                    "cama": mock_cama,
                    "fecha_ingreso": sample_episodio_data[0]["fecha_ingreso"],
                    "fecha_egreso": sample_episodio_data[0]["fecha_egreso"],
                    "tipo_actividad": "Hospitalización",
                    "especialidad": "Cardiología",
                    "inlier_outlier_flag": None,
                    "estancia_prequirurgica": None,
                    "estancia_postquirurgica": None,
                    "estancia_norma_grd": None,
                }
            )

            # Comprobar resultados internos
            assert importer.results["episodios"]["created"] == 1
            assert importer.results["episodios"]["updated"] == 0
            assert importer.results["episodios"]["errors"] == 0

def test_import_episodios_actualizacion(sample_episodio_data):
    importer = DatabaseImporter()

    mock_paciente = MagicMock()
    importer.episodio_to_paciente = {1: mock_paciente}
    mock_cama = MagicMock()
    
    with patch("api.management.modules.db_importer.DatabaseImporter._find_cama", return_value=mock_cama):
        with patch("api.models.Episodio.objects.get_or_create") as mock_get_or_create:
            # Simulamos episodio existente
            mock_episodio_instance = MagicMock()
            mock_episodio_instance.cama = None  # para probar actualización
            mock_get_or_create.return_value = (mock_episodio_instance, False)  # False = existente

            importer._import_episodios(sample_episodio_data)

            # Se debe llamar a save porque la cama era None
            assert mock_episodio_instance.save.called

            # Comprobar resultados internos
            assert importer.results["episodios"]["created"] == 0
            assert importer.results["episodios"]["updated"] == 1
            assert importer.results["episodios"]["errors"] == 0
