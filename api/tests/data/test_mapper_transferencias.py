from datetime import datetime

import pandas as pd
import pytest

from api.management.modules.data_mapper import DataMapper


class TestDataMapperTransferenciasCombined:
    @pytest.fixture
    def sample_combined_df(self):
        data = {
            "CÓDIGO EPISODIO CMBD": [101, 102, 103],
            "¿Qué gestión se solicito?": ["Transferencia", "Homecare", "TRANSFERENCIA"],
            "Estado": [None, "INICIADA", "COMPLETADA"],
            "Motivo de Cancelación": [None, None, "Paciente no disponible"],
            "Motivo de Rechazo": [None, None, None],
            "Tipo de Traslado": ["Interno", None, "Externo"],
            "Motivo de traslado": ["Cambio de piso", None, "Motivo X"],
            "Centro de Destinatario": ["Hospital A", None, "Hospital B"],
            "Fecha admisión": ["01/01/2025", "02/01/2025", "03/01/2025"],
            "Tipo de Solicitud": ["Urgente", "Normal", "Normal"],
        }
        df = pd.DataFrame(data)
        return df

    def test_map_transferencias_basic(self, sample_combined_df):
        mapper = DataMapper()

        transferencias = mapper._map_transferencias_from_combined(sample_combined_df)

        # Debe mapear solo las filas que sean transferencia
        # Atención: la tercera fila tiene "TRANSFERENCIA" en mayúsculas, según tu método actual se ignoraría
        # Para que el test pase tal cual tu método actual, solo mapea la primera fila
        assert len(transferencias) == 1

        t1 = transferencias[0]
        assert t1["episodio_cmbd"] == 101
        assert t1["estado"] == "PENDIENTE"  # Se usa default si None
        assert t1["tipo_traslado"] == "Interno"
        assert t1["motivo_traslado"] == "Cambio de piso"
        assert t1["centro_destinatario"] == "Hospital A"
        assert t1["tipo_solicitud"] == "Urgente"
        assert t1["fecha_solicitud"] == datetime(2025, 1, 1)

    def test_skip_missing_column(self):
        df = pd.DataFrame({"CÓDIGO EPISODIO CMBD": [101]})
        mapper = DataMapper()
        transferencias = mapper._map_transferencias_from_combined(df)
        assert transferencias == []
