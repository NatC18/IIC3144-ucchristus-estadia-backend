import pytest
import pandas as pd
from datetime import datetime
from api.management.modules.data_mapper import DataMapper

class TestDataMapperGestionesCombined:
    @pytest.fixture
    def sample_combined_df(self):
        data = {
            "CÓDIGO EPISODIO CMBD": [101, 102, 103, 104],
            "¿Qué gestión se solicito?": ["Homecare", "Transferencia", "Cobertura", None],
            "Fecha admisión": ["01/01/2025", "05/01/2025", None, "10/01/2025"],
            "Informe": ["Informe 1", "", None, "Informe 4"]
        }
        df = pd.DataFrame(data)
        return df

    def test_map_gestiones_basic(self, sample_combined_df, monkeypatch):
        mapper = DataMapper()

        # Mock de timezone.now para pruebas consistentes
        import django.utils.timezone as timezone
        fixed_now = datetime(2025, 1, 20, 12, 0, 0)
        monkeypatch.setattr(timezone, "now", lambda: fixed_now)

        gestiones = mapper._map_gestiones_from_combined(sample_combined_df)

        # Se espera mapear 2 gestiones (transferencia y None se ignoran)
        assert len(gestiones) == 2

        g1 = gestiones[0]
        assert g1["episodio_cmbd"] == 101
        assert g1["tipo_gestion"] == "HOMECARE"
        assert g1["estado_gestion"] == "INICIADA"
        assert g1["fecha_inicio"] == datetime(2025, 1, 1)
        assert g1["informe"] == "Informe 1"

        g2 = gestiones[1]
        assert g2["episodio_cmbd"] == 103
        assert g2["tipo_gestion"] == "COBERTURA"
        assert g2["estado_gestion"] == "INICIADA"
        # Fecha admisión es None, debe usar ahora
        assert g2["fecha_inicio"] == fixed_now
        # Informe es None -> generar por defecto
        assert g2["informe"] == "Gestión de tipo Cobertura"

    def test_skip_missing_column(self):
        # Si la columna de gestión no existe, se retorna lista vacía
        df = pd.DataFrame({"CÓDIGO EPISODIO CMBD": [101]})
        mapper = DataMapper()
        gestiones = mapper._map_gestiones_from_combined(df)
        assert gestiones == []

    def test_skip_transferencias(self):
        data = {
            "CÓDIGO EPISODIO CMBD": [101, 102],
            "¿Qué gestión se solicito?": ["Transferencia", "homecare"],
            "Fecha admisión": ["01/01/2025", "02/01/2025"],
            "Informe": ["Inf1", "Inf2"]
        }
        df = pd.DataFrame(data)
        mapper = DataMapper()
        gestiones = mapper._map_gestiones_from_combined(df)

        # Solo la segunda gestión se mapea
        assert len(gestiones) == 1
        assert gestiones[0]["tipo_gestion"] == "HOMECARE"


class TestDataMapperGestiones:
    @pytest.fixture
    def sample_df(self):
        data = {
            "episodio_cmbd": [101, 102, None],
            "tipo_gestion": ["HOMECARE", "Traslado", "COBERTURA"],
            "estado_gestion": ["INICIADA", None, "CERRADA"],
            "fecha_inicio": ["01/01/2025", "02/01/2025", "03/01/2025"],
            "fecha_fin": ["05/01/2025", None, "07/01/2025"],
            "observaciones": ["Obs1", "Obs2", "Obs3"],
            "usuario_responsable": ["user1@test.com", "user2@test.com", "user3@test.com"],
            "valor_gestion": [100.0, None, 200.0],
        }
        return pd.DataFrame(data)

    def test_map_gestiones_basic(self, sample_df):
        mapper = DataMapper()
        gestiones = mapper._map_gestiones(sample_df)

        # Solo se mapean los registros con episodio_cmbd y tipo_gestion válido
        assert len(gestiones) == 2

        g1 = gestiones[0]
        assert g1["episodio_cmbd"] == 101
        assert g1["tipo_gestion"] == "HOMECARE"
        assert g1["estado_gestion"] == "INICIADA"
        assert g1["fecha_inicio"] == datetime(2025, 1, 1)
        assert g1["fecha_fin"] == datetime(2025, 1, 5)
        assert g1["informe"] == "Obs1"
        assert g1["usuario_email"] == "user1@test.com"
        assert g1["valor_gestion"] == 100.0

        g2 = gestiones[1]
        assert g2["episodio_cmbd"] == 102
        assert g2["tipo_gestion"] == "TRASLADO"  # Uppercase
        assert g2["estado_gestion"] == "INICIADA"  # Fallback de _map_estado_gestion
        assert g2["fecha_inicio"] == datetime(2025, 1, 2)
        assert g2["fecha_fin"] is None
        assert g2["informe"] == "Obs2"
        assert g2["usuario_email"] == "user2@test.com"
        assert g2["valor_gestion"] is None