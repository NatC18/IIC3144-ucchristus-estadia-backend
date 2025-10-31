from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from api.management.modules.data_mapper import DataMapper


class TestDataMapperEpisodiosCombined:
    @pytest.fixture
    def sample_combined_df(self):
        # Simula un DataFrame combinado con episodios
        data = {
            "CÓDIGO EPISODIO CMBD": [101, 102, None, 104],
            "RUT": ["11.111.111-1", "22.222.222-2", "33.333.333-3", "44.444.444-4"],
            "Fecha Ingreso completa": ["01/01/2025", "05/01/2025", "10/01/2025", None],
            "Fecha alta": ["03/01/2025", None, "15/01/2025", "20/01/2025"],
            "Tipo Actividad": ["Cirugía", "Hospitalización", "Ambulatorio", "Urgencia"],
            "Estancia Inlier / Outlier": ["Inlier", "Outlier", None, "Inlier"],
            "Especialidad médica de la intervención (des)": [
                "Cardiología",
                "Traumatología",
                "Pediatría",
                None,
            ],
            "Estancias Prequirurgicas Int  -Episodio-": [1.0, 0.0, 2.5, None],
            "Estancias Postquirurgicas Int  -Episodio-": [2.0, 1.5, None, 3.0],
            "Estancia Norma GRD": [3.0, 4.0, 2.0, None],
            "CAMA": ["C001", "C002", "C003", "C004"],
        }
        df = pd.DataFrame(data)
        return df

    def test_map_episodios_basic(self, sample_combined_df):
        mapper = DataMapper()
        episodios = mapper._map_episodios_from_combined(sample_combined_df)

        # Solo se deben mapear los episodios que tienen CMBD y RUT
        assert len(episodios) == 3  # el tercero tiene CMBD=None y se ignora

        # Verificar primer episodio
        e1 = episodios[0]
        assert e1["episodio_cmbd"] == 101
        assert e1["rut_paciente"] == "11.111.111-1"
        assert e1["fecha_ingreso"] == datetime(2025, 1, 1)
        assert e1["fecha_egreso"] == datetime(2025, 1, 3)
        assert e1["tipo_actividad"] == "Cirugía"
        assert e1["inlier_outlier_flag"] == "Inlier"
        assert e1["especialidad"] == "Cardiología"
        assert e1["estancia_prequirurgica"] == 1.0
        assert e1["estancia_postquirurgica"] == 2.0
        assert e1["estancia_norma_grd"] == 3.0
        assert e1["codigo_cama"] == "C001"

        # Verificar segundo episodio (fecha_egreso=None, Excel2 vacío)
        e2 = episodios[1]
        assert e2["episodio_cmbd"] == 102
        assert e2["fecha_ingreso"] == datetime(2025, 1, 5)
        assert e2["fecha_egreso"] is None

        # Verificar cuarto episodio (fecha_ingreso=None)
        e3 = episodios[2]
        assert e3["episodio_cmbd"] == 104
        assert e3["fecha_ingreso"] is None
        assert e3["fecha_egreso"] == datetime(2025, 1, 20)


class TestDataMapperEpisodiosMapper:
    @pytest.fixture
    def sample_df(self):
        data = {
            "episodio_cmbd": [101, 102, None],
            "rut": ["11.111.111-1", "22.222.222-2", "33.333.333-3"],
            "nombre": ["María", "Carlos", "Test"],
            "fecha_ingreso": [
                "01/01/2025",
                None,
                "10/01/2025",
            ],  # La segunda fila sin fecha
            "fecha_alta": ["03/01/2025", "07/01/2025", None],
            "tipo_actividad": [None, "Cirugía", None],
            "servicio": ["Cardio", "Trauma", "Pediatría"],
            "cama": ["C001", "C002", "C003"],
            "habitacion": ["101", "102", "103"],
        }
        return pd.DataFrame(data)

    def test_map_episodios_basic(self, sample_df):
        mapper = DataMapper()
        episodios = mapper._map_episodios(sample_df)

        # Solo se deben mapear los que tienen episodio_cmbd
        assert len(episodios) == 2

        e1, e2 = episodios

        # Verificar que se mapean correctamente los campos
        assert e1["episodio_cmbd"] == 101
        assert e1["rut_paciente"] == "11.111.111-1"
        assert e1["fecha_ingreso"] == datetime(2025, 1, 1)

        assert e2["episodio_cmbd"] == 102
        assert e2["rut_paciente"] == "22.222.222-2"

        # La segunda fila tenía fecha_ingreso=None, debe usar fecha actual (datetime.now)
        # Solo verificar que sea un datetime
        assert isinstance(e2["fecha_ingreso"], datetime)
