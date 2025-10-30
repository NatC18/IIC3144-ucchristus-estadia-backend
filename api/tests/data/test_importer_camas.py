import pytest
from unittest.mock import patch, MagicMock
from api.management.modules.db_importer import DatabaseImporter

@pytest.fixture
def sample_cama_data():
    return [
        {
            "codigo_cama": "CAMA-001",
            "habitacion": "101A"
        },
        {
            "codigo_cama": "CAMA-002",  # Sin habitación, se genera por defecto
            "habitacion": None
        }
    ]

def test_import_camas_creacion(sample_cama_data):
    importer = DatabaseImporter()

    # Mock de get_or_create
    with patch("api.models.Cama.objects.get_or_create") as mock_get_or_create:
        # Simular que ambas camas no existen (created=True)
        mock_cama_instance_1 = MagicMock()
        mock_cama_instance_2 = MagicMock()

        # Configurar side_effect para devolver cada instancia
        mock_get_or_create.side_effect = [
            (mock_cama_instance_1, True),
            (mock_cama_instance_2, True)
        ]

        importer._import_camas(sample_cama_data)

        # Verificar que get_or_create fue llamado con la habitación correcta
        mock_get_or_create.assert_any_call(
            codigo_cama="CAMA-001",
            defaults={"habitacion": "101A"}
        )
        # Para la segunda, se genera habitación por defecto
        mock_get_or_create.assert_any_call(
            codigo_cama="CAMA-002",
            defaults={"habitacion": "HAB-CAMA-002"}
        )

        # Como es creación, save no debería llamarse
        assert not mock_cama_instance_1.save.called
        assert not mock_cama_instance_2.save.called

        # Verificar resultados internos
        assert importer.results["camas"]["created"] == 2
        assert importer.results["camas"]["updated"] == 0
        assert importer.results["camas"]["errors"] == 0

def test_import_camas_actualizacion(sample_cama_data):
    importer = DatabaseImporter()

    # Mock de get_or_create simulando que las camas ya existen
    with patch("api.models.Cama.objects.get_or_create") as mock_get_or_create:
        mock_cama_instance_1 = MagicMock()
        mock_cama_instance_1.habitacion = "100A"  # Diferente a la nueva

        mock_cama_instance_2 = MagicMock()
        mock_cama_instance_2.habitacion = "HAB-CAMA-002"  # Coincide con el valor por defecto

        mock_get_or_create.side_effect = [
            (mock_cama_instance_1, False),
            (mock_cama_instance_2, False)
        ]

        importer._import_camas(sample_cama_data)

        # La primera cama debe actualizarse porque habitacion cambió
        assert mock_cama_instance_1.save.called
        # La segunda no debe actualizarse
        assert not mock_cama_instance_2.save.called

        # Verificar resultados internos
        assert importer.results["camas"]["created"] == 0
        assert importer.results["camas"]["updated"] == 1
        assert importer.results["camas"]["errors"] == 0
