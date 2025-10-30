import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from api.management.modules.db_importer import DatabaseImporter

@pytest.fixture
def sample_gestion_data():
    return [
        {
            "episodio_cmbd": 1,
            "usuario_email": "doctor@hospital.cl",
            "tipo_gestion": "GESTION_CLINICA",
            "estado_gestion": "INICIADA",
            "fecha_inicio": datetime(2025, 10, 29, 12, 0),
            "fecha_fin": datetime(2025, 10, 29, 14, 0),
            "informe": "Informe de prueba",
        }
    ]

def test_import_gestiones_creacion(sample_gestion_data):
    importer = DatabaseImporter()

    # Mock de Episodio.objects.get
    mock_episodio = MagicMock()
    with patch("api.models.Episodio.objects.get", return_value=mock_episodio):
        # Mock de User.objects.get
        mock_usuario = MagicMock()
        with patch("api.management.modules.db_importer.User.objects.get", return_value=mock_usuario):
            # Mock de Gestion.objects.create
            with patch("api.models.Gestion.objects.create") as mock_create:
                mock_gestion_instance = MagicMock()
                mock_create.return_value = mock_gestion_instance

                importer._import_gestiones(sample_gestion_data)

                # Comprobar que create se llamó con los valores correctos
                mock_create.assert_called_once_with(
                    episodio=mock_episodio,
                    usuario=mock_usuario,
                    tipo_gestion="GESTION_CLINICA",
                    estado_gestion="INICIADA",
                    fecha_inicio=sample_gestion_data[0]["fecha_inicio"],
                    fecha_fin=sample_gestion_data[0]["fecha_fin"],
                    informe="Informe de prueba"
                )

                # Comprobar resultados internos
                assert importer.results["gestiones"]["created"] == 1
                assert importer.results["gestiones"]["errors"] == 0
