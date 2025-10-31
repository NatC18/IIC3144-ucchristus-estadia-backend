from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from api.services import processors


@pytest.fixture
def archivo_mock():
    mock = MagicMock()
    mock.estado = "PENDIENTE"
    mock.errores = []
    mock.save = MagicMock()
    mock.agregar_error = MagicMock()
    mock.actualizar_progreso = MagicMock()
    mock.filas_totales = 0
    mock.filas_errores = 0
    return mock


@pytest.fixture
def base_processor(archivo_mock):
    p = processors.GestionExcelProcessor(archivo_mock)
    p.df = pd.DataFrame(columns=p.get_columnas_requeridas())
    return p


# -------------------------------
# 🔹 Métodos auxiliares
# -------------------------------


def test_validar_rut_formatos_validos(base_processor):
    assert base_processor._validar_rut("12.345.678-9")
    assert base_processor._validar_rut("12345678-9")
    assert not base_processor._validar_rut("1234")
    assert not base_processor._validar_rut(None)


def test_convertir_fecha_formats(base_processor):
    today = date.today()
    assert base_processor._convertir_fecha(today) == today
    result = base_processor._convertir_fecha(datetime(2024, 5, 1))
    assert isinstance(result, (datetime, date))
    assert (
        result.date() == date(2024, 5, 1)
        if isinstance(result, datetime)
        else result == date(2024, 5, 1)
    )
    assert base_processor._convertir_fecha("2024-05-01") == date(2024, 5, 1)
    assert base_processor._convertir_fecha("01/05/2024") == date(2024, 5, 1)
    with pytest.raises(ValueError):
        base_processor._convertir_fecha("no-es-fecha")


def test_convertir_fecha_excel_formats():
    p = processors.PacienteEpisodioExcelProcessor(MagicMock())
    assert p._convertir_fecha_excel(45300) == date(2024, 1, 9)
    assert p._convertir_fecha_excel("2024-01-01") == date(2024, 1, 1)

    result = p._convertir_fecha_excel(datetime(2024, 1, 1))
    if isinstance(result, datetime):
        result = result.date()
    assert result == date(2024, 1, 1)

    with pytest.raises(ValueError):
        p._convertir_fecha_excel(None)
    with pytest.raises(ValueError):
        p._convertir_fecha_excel("no-es-fecha")


# -------------------------------
# 🔹 UserExcelProcessor
# -------------------------------


@patch("api.services.processors.User")
def test_user_processor_validations(mock_user, archivo_mock):
    p = processors.UserExcelProcessor(archivo_mock)
    p.df = pd.DataFrame(columns=p.get_columnas_requeridas())
    assert p._validar_estructura()

    mock_user.objects.filter.return_value.exists.return_value = True
    data = {
        "email": "duplicado@test.com",
        "nombre": "A",
        "apellido": "B",
        "rol": "ADMIN",
    }
    result = p._validar_fila(data, 2)
    assert result is None
    assert archivo_mock.agregar_error.called


@patch("api.services.processors.User")
def test_user_processor_success(mock_user, archivo_mock):
    p = processors.UserExcelProcessor(archivo_mock)
    datos = {"email": "ok@test.com", "nombre": "A", "apellido": "B", "rol": "ADMIN"}
    p._procesar_fila_modelo(datos, 2)
    mock_user.objects.create.assert_called_once()


# -------------------------------
# 🔹 PacienteExcelProcessor
# -------------------------------


@patch("api.services.processors.Paciente")
def test_paciente_validaciones(mock_pac, archivo_mock):
    p = processors.PacienteExcelProcessor(archivo_mock)
    p.df = pd.DataFrame(columns=p.get_columnas_requeridas())
    assert p._validar_estructura()

    mock_pac.objects.filter.return_value.exists.return_value = True
    data = {
        "rut": "12345678-9",
        "nombre": "Juan",
        "sexo": "X",
        "fecha_nacimiento": "3000-01-01",
        "prevision": "X",
    }
    result = p._validar_fila(data, 2)
    assert result is None
    assert archivo_mock.agregar_error.called


@patch("api.services.processors.Paciente")
def test_paciente_procesamiento(mock_pac, archivo_mock):
    p = processors.PacienteExcelProcessor(archivo_mock)
    datos = {
        "rut": "12345678-9",
        "nombre": "Ana",
        "sexo": "F",
        "fecha_nacimiento": "2000-01-01",
        "prevision": "FONASA",
    }
    p._procesar_fila_modelo(datos, 2)
    mock_pac.objects.create.assert_called_once()


# -------------------------------
# 🔹 CamaExcelProcessor
# -------------------------------


@patch("api.services.processors.Cama")
def test_cama_validaciones(mock_cama, archivo_mock):
    p = processors.CamaExcelProcessor(archivo_mock)
    p.df = pd.DataFrame(columns=p.get_columnas_requeridas())
    assert p._validar_estructura()

    mock_cama.objects.filter.return_value.exists.return_value = True
    data = {"numero": "1", "ubicacion": "", "tipo": "DESCONOCIDO", "estado": "X"}
    result = p._validar_fila(data, 2)
    assert result is None


@patch("api.services.processors.Cama")
def test_cama_procesamiento(mock_cama, archivo_mock):
    p = processors.CamaExcelProcessor(archivo_mock)
    datos = {"numero": "1", "ubicacion": "A", "tipo": "UCI", "estado": "DISPONIBLE"}
    p._procesar_fila_modelo(datos, 2)
    mock_cama.objects.create.assert_called_once()


# -------------------------------
# 🔹 EpisodioExcelProcessor
# -------------------------------


@patch("api.services.processors.Paciente")
@patch("api.services.processors.Cama")
def test_episodio_validaciones(mock_cama, mock_pac, archivo_mock):
    p = processors.EpisodioExcelProcessor(archivo_mock)
    p.df = pd.DataFrame(columns=p.get_columnas_requeridas())
    assert p._validar_estructura()

    mock_pac.DoesNotExist = Exception
    mock_cama.DoesNotExist = Exception
    mock_pac.objects.get.side_effect = Exception("No existe")
    mock_cama.objects.get.side_effect = Exception("No existe")

    data = {
        "paciente_rut": "1",
        "cama_numero": "2",
        "fecha_ingreso": "no",
        "tipo_episodio": "X",
    }
    result = p._validar_fila(data, 2)
    assert result is None


@patch("api.services.processors.Episodio")
def test_episodio_procesamiento(mock_epi, archivo_mock):
    p = processors.EpisodioExcelProcessor(archivo_mock)
    datos = {
        "paciente": MagicMock(),
        "cama": MagicMock(),
        "fecha_ingreso_parsed": date.today(),
        "tipo_episodio": "AMBULATORIO",
    }
    p._procesar_fila_modelo(datos, 2)
    mock_epi.objects.create.assert_called_once()


# -------------------------------
# 🔹 GestionExcelProcessor
# -------------------------------


@patch("api.services.processors.Episodio")
@patch("api.services.processors.User")
def test_gestion_validaciones(mock_user, mock_epi, archivo_mock):
    p = processors.GestionExcelProcessor(archivo_mock)
    p.df = pd.DataFrame(columns=p.get_columnas_requeridas())
    assert p._validar_estructura()

    mock_epi.DoesNotExist = Exception
    mock_user.DoesNotExist = Exception
    mock_epi.objects.get.side_effect = Exception("No existe episodio")
    mock_user.objects.get.side_effect = Exception("No existe user")

    data = {"episodio_id": "1", "usuario_email": "x", "tipo_gestion": "X"}
    result = p._validar_fila(data, 2)
    assert result is None


@patch("api.services.processors.Gestion")
def test_gestion_procesamiento(mock_gest, archivo_mock):
    p = processors.GestionExcelProcessor(archivo_mock)
    datos = {
        "episodio": MagicMock(),
        "usuario": MagicMock(),
        "tipo_gestion": "CLINICA",
        "fecha_gestion_parsed": date.today(),
    }
    p._procesar_fila_modelo(datos, 2)
    mock_gest.objects.create.assert_called_once()


def test_convertir_fecha_excel_errores():
    p = processors.PacienteEpisodioExcelProcessor(MagicMock())

    # Valor NaN
    import numpy as np

    with pytest.raises(ValueError):
        p._convertir_fecha_excel(np.nan)

    # Float no convertible
    with pytest.raises(ValueError):
        p._convertir_fecha_excel(999999999999)

    # String con formato inválido
    with pytest.raises(ValueError):
        p._convertir_fecha_excel("32/13/2020")

    # Tipo no soportado
    with pytest.raises(ValueError):
        p._convertir_fecha_excel([])  # lista


def test_validar_rut_varios_formatos():
    p = processors.PacienteEpisodioExcelProcessor(MagicMock())
    assert p._validar_rut("12.345.678-9")
    assert p._validar_rut("12345678-9")
    assert not p._validar_rut("1234")
    assert not p._validar_rut(None)
    assert not p._validar_rut("abcdefgh")


@patch("api.services.processors.Paciente")
def test_crear_o_actualizar_paciente(mock_pac):
    p = processors.PacienteEpisodioExcelProcessor(MagicMock())

    # Caso 1: Paciente existe y se actualiza nombre
    mock_instance = MagicMock(nombre="Antiguo")
    mock_pac.objects.get.return_value = mock_instance
    datos = {"rut_paciente": "12345678-9", "nombre_paciente": "Nuevo"}
    result = p._crear_o_actualizar_paciente(datos)
    assert result == mock_instance
    mock_instance.save.assert_called_once()

    # Caso 2: Paciente no existe, se crea nuevo
    class DummyDoesNotExist(Exception):
        pass

    mock_pac.DoesNotExist = DummyDoesNotExist
    mock_pac.objects.get.side_effect = DummyDoesNotExist
    mock_pac.objects.create.return_value = MagicMock()

    datos = {"rut_paciente": "98765432-1", "nombre_paciente": "Ana"}
    result = p._crear_o_actualizar_paciente(datos)
    mock_pac.objects.create.assert_called_once()


@patch("api.services.processors.Episodio")
@patch("api.services.processors.timezone")
def test_crear_episodio(mock_tz, mock_epi):
    p = processors.PacienteEpisodioExcelProcessor(MagicMock())
    mock_tz.make_aware.side_effect = lambda x: x  # Evita timezone real

    datos = {
        "cama_obj": MagicMock(),
        "episodio_cmbd": 1,
        "fecha_admision_parsed": date(2024, 1, 1),
        "categoria_tratamiento": "Hospitalización",
        "desc_enfermeria": "Cirugía",
    }
    paciente = MagicMock()
    p._crear_episodio(datos, paciente)
    mock_epi.objects.create.assert_called_once()


@patch("api.services.processors.Cama")
@patch("api.services.processors.Episodio")
def test_validar_fila_con_errores(mock_epi, mock_cama, archivo_mock):
    p = processors.PacienteEpisodioExcelProcessor(archivo_mock)
    mock_cama.DoesNotExist = Exception
    mock_cama.objects.get.side_effect = Exception("No existe cama")

    data = {
        "rut_paciente": "no-valido",
        "nombre_paciente": "",
        "episodio": "abc",  # no numérico
        "habitacion": "H1",
        "cama": "C1",
        "categoria_tratamiento": "",
        "fecha_admision": "no-es-fecha",
    }

    result = p._validar_fila(data, 2)
    assert result is None
    archivo_mock.agregar_error.assert_called()


def test_procesar_fila_modelo_error(monkeypatch, archivo_mock):
    p = processors.PacienteEpisodioExcelProcessor(archivo_mock)
    datos = {"rut_paciente": "12345678-9", "nombre_paciente": "Ana"}

    def fail_crear(*args, **kwargs):
        raise Exception("Error simulado")

    monkeypatch.setattr(p, "_crear_o_actualizar_paciente", fail_crear)
    with pytest.raises(Exception):
        p._procesar_fila_modelo(datos, 1)

    archivo_mock.agregar_error.assert_called()


@patch("api.services.processors.User")
def test_user_processor_errores(mock_user, archivo_mock):
    p = processors.UserExcelProcessor(archivo_mock)

    # Email inválido
    data = {"email": "invalido@", "nombre": "A", "apellido": "B", "rol": "ADMIN"}
    p._validar_fila(data, 1)
    archivo_mock.agregar_error.assert_called()

    # Rol inválido
    data = {"email": "ok@test.com", "nombre": "A", "apellido": "B", "rol": "INVALIDO"}
    p._validar_fila(data, 2)
    archivo_mock.agregar_error.assert_called()

    # RUT mal formado
    data = {
        "email": "ok@test.com",
        "nombre": "A",
        "apellido": "B",
        "rol": "ADMIN",
        "rut": "1234",
    }
    p._validar_fila(data, 3)
    archivo_mock.agregar_error.assert_called()


@patch("api.services.processors.Paciente")
def test_paciente_processor_errores(mock_pac, archivo_mock):
    p = processors.PacienteExcelProcessor(archivo_mock)
    mock_pac.objects.filter.return_value.exists.return_value = False

    # Previsión inválida
    data = {
        "rut": "12345678-9",
        "nombre": "Juan",
        "sexo": "M",
        "fecha_nacimiento": "2000-01-01",
        "prevision": "INVALIDA",
    }
    p._validar_fila(data, 1)
    archivo_mock.agregar_error.assert_called()

    # Fecha futura
    futura = date.today().replace(year=date.today().year + 1)
    data["fecha_nacimiento"] = futura.strftime("%Y-%m-%d")
    p._validar_fila(data, 2)
    archivo_mock.agregar_error.assert_called()


@patch("api.services.processors.Cama")
def test_cama_processor_errores(mock_cama, archivo_mock):
    p = processors.CamaExcelProcessor(archivo_mock)
    mock_cama.objects.filter.return_value.exists.return_value = False

    # Tipo inválido
    data = {"numero": "1", "ubicacion": "A", "tipo": "RARO", "estado": "DISPONIBLE"}
    p._validar_fila(data, 1)
    archivo_mock.agregar_error.assert_called()

    # Estado inválido
    data = {"numero": "1", "ubicacion": "A", "tipo": "UCI", "estado": "INEXISTENTE"}
    p._validar_fila(data, 2)
    archivo_mock.agregar_error.assert_called()


@patch("api.services.processors.Cama")
@patch("api.services.processors.Paciente")
def test_episodio_processor_errores(mock_pac, mock_cama, archivo_mock):
    p = processors.EpisodioExcelProcessor(archivo_mock)
    mock_pac.objects.get.side_effect = mock_pac.DoesNotExist
    mock_cama.objects.get.side_effect = mock_cama.DoesNotExist

    data = {
        "paciente_rut": "123",
        "cama_numero": "1",
        "fecha_ingreso": "no-es-fecha",
        "fecha_egreso": "2000-01-01",
        "tipo_episodio": "INVALIDO",
    }
    p._validar_fila(data, 1)
    archivo_mock.agregar_error.assert_called()


@patch("api.services.processors.User")
@patch("api.services.processors.Episodio")
def test_gestion_processor_errores(mock_epi, mock_user, archivo_mock):
    p = processors.GestionExcelProcessor(archivo_mock)
    mock_epi.objects.get.side_effect = mock_epi.DoesNotExist
    mock_user.objects.get.side_effect = mock_user.DoesNotExist

    # Fecha con formato inválido
    data = {
        "episodio_id": "1",
        "usuario_email": "x",
        "tipo_gestion": "INVALIDA",
        "fecha_gestion": "no-fecha",
    }
    p._validar_fila(data, 2)
    archivo_mock.agregar_error.assert_called()

    # Fecha ausente → debería asignar date.today()
    data = {"episodio_id": "1", "usuario_email": "x", "tipo_gestion": "CLINICA"}
    result = p._validar_fila(data, 3)
    assert "fecha_gestion_parsed" in result


def test_convertir_fecha_excel_otros_formatos():
    p = processors.PacienteEpisodioExcelProcessor(MagicMock())

    # formato con puntos
    assert p._convertir_fecha_excel("01.02.2023") == date(2023, 2, 1)

    # tipo no soportado
    with pytest.raises(ValueError):
        p._convertir_fecha_excel(set([1, 2]))
