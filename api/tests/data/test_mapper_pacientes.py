import pytest
import pandas as pd
from datetime import datetime
from api.management.modules.data_mapper import DataMapper

class TestDataMapperPacientesCombined:
    @pytest.fixture
    def sample_combined_df(self):
        # Simula un DataFrame combinado
        data = {
            "RUT": ["11.111.111-1", "22.222.222-2", None],
            "Nombre": ["María González Pérez", "Carlos Martínez Silva", "Paciente Sin RUT"],
            "Sexo  (Desc)": ["Femenino", "Masculino", "F"],
            "Fecha de Nacimiento": ["15/05/1980", "22/08/1975", "01/01/1990"],
            "Convenio": ["FONASA", "ISAPRE", "FONASA"],
            "Nombre de la aseguradora": [None, None, None],
        }
        df = pd.DataFrame(data)
        return df

    def test_map_pacientes_basic(self, sample_combined_df):
        mapper = DataMapper()
        pacientes = mapper._map_pacientes_from_combined(sample_combined_df)

        assert len(pacientes) == 2

        p1 = pacientes[0]
        assert p1["rut"] == "11.111.111-1"
        assert p1["nombre"] == "María González Pérez"
        assert p1["sexo"] == "F"
        assert p1["fecha_nacimiento"] == datetime(1980, 5, 15)
        assert p1["prevision_1"] == "FONASA"
        assert p1["prevision_2"] is None

        p2 = pacientes[1]
        assert p2["rut"] == "22.222.222-2"
        assert p2["nombre"] == "Carlos Martínez Silva"
        assert p2["sexo"] == "M"
        assert p2["fecha_nacimiento"] == datetime(1975, 8, 22)
        assert p2["prevision_1"] == "ISAPRE"
        assert p2["prevision_2"] is None

    def test_skip_missing_rut(self, sample_combined_df):
        mapper = DataMapper()
        pacientes = mapper._map_pacientes_from_combined(sample_combined_df)

        # El paciente sin RUT no debe estar en la lista
        ruts = [p["rut"] for p in pacientes]
        assert None not in ruts
        assert "Paciente Sin RUT" not in [p["nombre"] for p in pacientes]

    def test_prevision_2_logic(self):
        # Caso donde Convenio es None, pero Nombre de la aseguradora existe
        data = {
            "RUT": ["33.333.333-3"],
            "Nombre": ["Test Usuario"],
            "Sexo  (Desc)": ["F"],
            "Fecha de Nacimiento": ["01/01/1990"],
            "Convenio": [None],
            "Nombre de la aseguradora": ["ISAPRE TEST"],
        }
        df = pd.DataFrame(data)
        mapper = DataMapper()
        pacientes = mapper._map_pacientes_from_combined(df)

        assert pacientes[0]["prevision_1"] == "ISAPRE TEST"
        assert pacientes[0]["prevision_2"] is None
