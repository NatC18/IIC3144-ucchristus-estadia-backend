import pytest
from unittest.mock import patch
from api.management.modules.data_mapper import DataMapper

class TestDataMapperCleanRUT:
    @pytest.fixture
    def mapper(self):
        return DataMapper()

    @pytest.mark.parametrize(
        "input_rut,expected",
        [
            ("11111111-1", "11.111.111-1"),        # sin puntos ni guión
            ("11a111b111-1", "11.111.111-1"),      # caracteres extraños
            ("1111111-8", "1.111.111-8"),          # demasiado corto pero entra a formato
            ("11.111.111-1", "11.111.111-1"),      # ya formateado
        ]
    )
    def test_clean_rut_with_re(self, mapper, input_rut, expected):
        # Forzar que _validate_rut_format devuelva False para entrar al bloque re
        with patch.object(mapper, "_validate_rut_format", return_value=False):
            result = mapper._clean_rut(input_rut)
            assert result == expected

    def test_clean_rut_none_or_empty(self, mapper):
        assert mapper._clean_rut(None) is None
        assert mapper._clean_rut("") is None
