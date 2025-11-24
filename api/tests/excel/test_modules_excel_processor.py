import logging
from pathlib import Path

import pandas as pd
import pytest

from api.management.modules.excel_processor import ExcelProcessor


@pytest.fixture
def processor():
    """Fixture simple para inicializar ExcelProcessor en todos los tests."""
    return ExcelProcessor()


@pytest.fixture
def sample_excel_files(tmp_path):
    """Fixture: crea tres archivos Excel válidos con columnas realistas"""
    df1 = pd.DataFrame(
        {
            "CÓDIGO EPISODIO CMBD": ["EP001", "EP002"],
            "RUT": ["12.345.678-9", "98.765.432-1"],  # 🔹 agrega esta línea
            "Tipo Actividad": ["Consulta", "Urgencia"],
            "Estancia Inlier / Outlier": ["Inlier", "Outlier"],
            "Especialidad médica de la intervención (des)": ["Cardiología", "Trauma"],
        }
    )
    df2 = pd.DataFrame(
        {
            "Episodio:": ["EP001", "EP002"],
            "RUT": ["12.345.678-9", "98.765.432-1"],
            "Nombre": ["Juan Pérez", "María López"],
            "Status": ["Activo", "Alta"],
            "Fecha de Nacimiento": ["1980-01-01", "1990-01-01"],
            "Sexo  (Desc)": ["MASCULINO", "FEMENINO"],
            "Edad en años": [43, 33],
            "Prevision (Desc)": ["FONASA", "ISAPRE"],
        }
    )
    df3 = pd.DataFrame(
        {
            "episodio": ["EP001", "EP002"],
            "cama": ["101", "102"],
            "HABITACION": ["H101", "H102"],
            "MEDICO_TRATANTE": ["Dr. Juan", "Dra. María"],
        }
    )

    df4 = pd.DataFrame(
        {
            "Episodio / Estadía": ["EP001", "EP002"],
            "Puntaje": ["3", "7"]
        }
    )
    path1 = tmp_path / "excel1.xlsx"
    path2 = tmp_path / "excel2.xlsx"
    path3 = tmp_path / "excel3.xlsx"
    path4 = tmp_path / "excel4.xlsx"
    df1.to_excel(path1, index=False)
    df2.to_excel(path2, index=False)
    df3.to_excel(path3, index=False)
    df4.to_excel(path4, index=False)
    return {"excel1": path1, "excel2": path2, "excel3": path3, "excel4": path4}


# --- 🔹 Inicialización y carga ---
def test_init():
    processor = ExcelProcessor()
    assert processor.combined_df is None
    assert processor.excel1_df is None


def test_load_excel_files_success(sample_excel_files):
    processor = ExcelProcessor()
    assert processor.load_excel_files(sample_excel_files) is True
    assert len(processor.excel2_df) == 2


def test_load_excel_files_missing_file(sample_excel_files):
    del sample_excel_files["excel1"]
    processor = ExcelProcessor()
    assert processor.load_excel_files(sample_excel_files) is False


def test_load_single_excel_invalid(tmp_path):
    """Simula archivo sin columna episodio"""
    invalid_path = tmp_path / "invalid.xlsx"
    pd.DataFrame({"col": [1, 2]}).to_excel(invalid_path, index=False)
    processor = ExcelProcessor()
    result = processor._load_single_excel(invalid_path, "excel1")
    assert result is None


# --- 🔹 Combinación de datos ---
def test_combine_data_without_files():
    processor = ExcelProcessor()
    assert processor.combine_data() is False


def test_combine_data_success(sample_excel_files):
    processor = ExcelProcessor()
    processor.load_excel_files(sample_excel_files)
    assert processor.combine_data() is True
    assert "episodio_cmbd" in processor.combined_df.columns
    assert len(processor.combined_df) == 2


def test_clean_episodio_data_removes_invalids():
    df = pd.DataFrame({"episodio_cmbd": ["EP001", "", None, "EP002"]})
    processor = ExcelProcessor()
    cleaned = processor._clean_episodio_data(df, "test")
    assert len(cleaned) == 2


def test_rename_columns_with_suffix():
    df = pd.DataFrame({"episodio_cmbd": ["EP1"], "valor": [10]})
    processor = ExcelProcessor()
    renamed = processor._rename_columns_with_suffix(df, "_extra")
    assert "valor_extra" in renamed.columns
    assert "episodio_cmbd" in renamed.columns


def test_normalize_episodio_column_variants():
    df = pd.DataFrame({"Episodio:": ["EP1", "EP2"], "X": [1, 2]})
    processor = ExcelProcessor()
    normalized = processor._normalize_episodio_column(df, "test")
    assert "episodio_cmbd" in normalized.columns


# --- 🔹 Resumen y exportación ---
def test_get_data_summary(sample_excel_files):
    processor = ExcelProcessor()
    processor.load_excel_files(sample_excel_files)
    processor.combine_data()
    summary = processor.get_data_summary()
    assert summary["files_loaded"]["excel1"] is True
    assert "total_rows" in summary["combined_stats"]


def test_export_combined_data_success(tmp_path):
    processor = ExcelProcessor()
    processor.combined_df = pd.DataFrame({"episodio_cmbd": ["E1"], "data": [10]})
    out = tmp_path / "out.xlsx"
    assert processor.export_combined_data(out) is True
    assert out.exists()


def test_export_combined_data_without_df(tmp_path):
    processor = ExcelProcessor()
    assert processor.export_combined_data(tmp_path / "x.xlsx") is False


# --- 🔹 Extracción de datos de paciente ---
def test_extract_patient_fields(sample_excel_files):
    processor = ExcelProcessor()
    processor.load_excel_files(sample_excel_files)
    processor.combine_data()
    row = processor.combined_df.iloc[0]

    assert processor._extract_rut(row) == "12.345.678-9"
    assert processor._extract_nombre(row) == "Juan Pérez"
    assert processor._extract_fecha_nacimiento(row) == "1980-01-01"
    assert processor._extract_sexo(row) == "M"
    assert processor._extract_edad(row) == 43
    assert processor._extract_prevision(row) == "FONASA"


# --- 🔹 Extracción de datos de episodio ---
def test_extract_episodio_fields(sample_excel_files):
    processor = ExcelProcessor()
    processor.load_excel_files(sample_excel_files)
    processor.combine_data()
    row = processor.combined_df.iloc[0]

    assert isinstance(processor._extract_servicio(row), str)
    assert isinstance(processor._extract_cama(row), str)
    assert isinstance(processor._extract_diagnostico(row), str)
    assert isinstance(processor._extract_tipo_actividad(row), str)
    assert isinstance(processor._extract_estado_episodio(row), str)
    assert isinstance(processor._extract_estancia(row), int)


# --- 🔹 Extracción de datos de gestión ---
def test_extract_gestion_fields(sample_excel_files):
    processor = ExcelProcessor()
    processor.load_excel_files(sample_excel_files)
    processor.combine_data()
    row = processor.combined_df.iloc[0]

    assert isinstance(processor._extract_tipo_gestion(row), str)
    assert isinstance(processor._extract_estado_gestion(row), str)
    assert isinstance(processor._extract_valor_gestion(row), float)
    assert isinstance(processor._extract_observaciones_gestion(row), str)
    assert isinstance(processor._extract_usuario_responsable(row), str)


# --- 🔹 Preparación de datos para modelos ---
def test_prepare_data_for_models(sample_excel_files):
    processor = ExcelProcessor()
    processor.load_excel_files(sample_excel_files)
    processor.combine_data()
    data = processor.clean_data_for_models()
    assert "pacientes" in data
    assert "episodios" in data
    assert "gestiones" in data


def test_prepare_data_for_models_without_combined():
    processor = ExcelProcessor()
    result = processor.clean_data_for_models()
    assert result == {}


# --- 🔹 Proceso completo de archivos locales ---
def test_process_local_files(sample_excel_files):
    processor = ExcelProcessor()
    result = processor.process_local_files(
        {k: str(v) for k, v in sample_excel_files.items()}
    )
    assert "excel1" in result
    assert "combined" in result
    assert len(result["combined"]) > 0


# --- 🔹 Casos de error extremos ---
def test_combine_data_with_missing_column(sample_excel_files):
    processor = ExcelProcessor()
    processor.load_excel_files(sample_excel_files)
    processor.excel1_df.drop(columns=["episodio_cmbd"], inplace=True)
    result = processor.combine_data()
    assert result is False


def test_load_excel_with_exception(monkeypatch, tmp_path):
    bad_path = tmp_path / "bad.xlsx"
    pd.DataFrame().to_excel(bad_path, index=False)

    def fake_read_excel(*args, **kwargs):
        raise ValueError("fail")

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)
    processor = ExcelProcessor()
    result = processor._load_single_excel(bad_path, "excel1")
    assert result is None


def test_combine_data_empty_dataframes(monkeypatch):
    processor = ExcelProcessor()
    processor.excel1_df = pd.DataFrame()
    processor.excel2_df = pd.DataFrame()
    processor.excel3_df = pd.DataFrame()
    assert processor.combine_data() is False


def test_load_single_excel_file_not_found(tmp_path):
    processor = ExcelProcessor()
    fake_path = tmp_path / "missing.xlsx"
    result = processor._load_single_excel(fake_path, "excel1")
    assert result is None


def test_clean_episodio_data_with_no_column():
    df = pd.DataFrame({"otra_col": [1, 2, 3]})
    processor = ExcelProcessor()
    result = processor._clean_episodio_data(df, "test")
    assert "episodio_cmbd" not in result.columns or len(result) == 0


def test_export_combined_data_invalid_path(tmp_path):
    processor = ExcelProcessor()
    processor.combined_df = pd.DataFrame({"a": [1]})
    bad_path = tmp_path / "no_dir" / "file.xlsx"
    assert processor.export_combined_data(bad_path) is False


def test_get_data_summary_without_combined(monkeypatch):
    processor = ExcelProcessor()
    processor.excel1_df = pd.DataFrame({"episodio_cmbd": []})
    processor.excel2_df = pd.DataFrame({"episodio_cmbd": []})
    processor.excel3_df = pd.DataFrame({"episodio_cmbd": []})
    processor.excel4_df = pd.DataFrame({"episodio_cmbd": []})

    summary = processor.get_data_summary()
    assert isinstance(summary, dict)
    expected_keys = {"row_counts", "column_counts", "files_loaded", "combined_stats"}
    assert expected_keys.issubset(summary.keys())
    assert all(v == 0 for v in summary["row_counts"].values())
    assert all(summary["files_loaded"].values())


def test_logger_called_on_error(monkeypatch, caplog):
    processor = ExcelProcessor()

    def bad_load_excel(*args, **kwargs):
        raise Exception("error for test")

    monkeypatch.setattr(processor, "_load_single_excel", bad_load_excel)
    files = {"excel1": "fake1.xlsx", "excel2": "fake2.xlsx", "excel3": "fake3.xlsx", "excel4": "fake4.xlsx"}
    with caplog.at_level(logging.ERROR):
        processor.load_excel_files(files)
    assert "error for test" in caplog.text or "Faltan archivos" in caplog.text


def test_returns_false_when_excel1_fails(monkeypatch, processor):
    """
    Cubre el caso en que _load_single_excel devuelve None para excel1
    → Debe retornar False inmediatamente.
    """
    calls = []

    def fake_loader(path, name):
        calls.append(name)
        return None if name == "excel1" else pd.DataFrame()

    monkeypatch.setattr(processor, "_load_single_excel", fake_loader)
    result = processor.load_excel_files(
        {"excel1": "mock1.xlsx", "excel2": "mock2.xlsx", "excel3": "mock3.xlsx", "excel4": "mock4.xlsx"}
    )
    assert result is False
    assert calls == ["excel1"]  # se corta antes de excel2


def test_returns_false_when_excel2_fails(monkeypatch, processor):
    """
    Cubre el caso en que _load_single_excel devuelve None para excel2
    → Debe retornar False después de leer excel1.
    """
    calls = []

    def fake_loader(path, name):
        calls.append(name)
        if name == "excel2":
            return None
        return pd.DataFrame()

    monkeypatch.setattr(processor, "_load_single_excel", fake_loader)
    result = processor.load_excel_files(
        {"excel1": "mock1.xlsx", "excel2": "mock2.xlsx", "excel3": "mock3.xlsx", "excel4": "mock4.xlsx"}
    )
    assert result is False
    assert calls == ["excel1", "excel2"]


def test_returns_false_when_excel3_fails(monkeypatch, processor):
    """
    Cubre el caso en que _load_single_excel devuelve None para excel3
    → Debe retornar False al final de la secuencia.
    """
    calls = []

    def fake_loader(path, name):
        calls.append(name)
        if name == "excel3":
            return None
        return pd.DataFrame()

    monkeypatch.setattr(processor, "_load_single_excel", fake_loader)
    result = processor.load_excel_files(
        {"excel1": "mock1.xlsx", "excel2": "mock2.xlsx", "excel3": "mock3.xlsx", "excel4": "mock4.xlsx"}
    )
    assert result is False
    assert calls == ["excel1", "excel2", "excel3"]


# === 🔹 Casos extra: cobertura de try/except y retornos False ===


def test_load_excel_files_exception_during_excel1(monkeypatch, processor):
    """
    Simula que _load_single_excel lanza excepción al leer excel1.
    Cubre el bloque try/except inicial (líneas ~122–125).
    """

    def raise_on_excel1(path, name):
        if name == "excel1":
            raise ValueError("excel1 failed")
        return pd.DataFrame()

    monkeypatch.setattr(processor, "_load_single_excel", raise_on_excel1)
    result = processor.load_excel_files(
        {"excel1": "mock1.xlsx", "excel2": "mock2.xlsx", "excel3": "mock3.xlsx", "excel4": "mock4.xlsx"}
    )
    assert result is False


def test_load_excel_files_exception_during_excel2(monkeypatch, processor):
    """
    Simula que _load_single_excel lanza excepción al leer excel2.
    Cubre el bloque try/except medio (líneas ~138).
    """

    def raise_on_excel2(path, name):
        if name == "excel2":
            raise ValueError("excel2 failed")
        return pd.DataFrame()

    monkeypatch.setattr(processor, "_load_single_excel", raise_on_excel2)
    result = processor.load_excel_files(
        {"excel1": "mock1.xlsx", "excel2": "mock2.xlsx", "excel3": "mock3.xlsx", "excel4": "mock4.xlsx"}
    )
    assert result is False


def test_load_excel_files_exception_during_excel3(monkeypatch, processor):
    """
    Simula que _load_single_excel lanza excepción al leer excel3.
    Cubre el bloque try/except final del método.
    """

    def raise_on_excel3(path, name):
        if name == "excel3":
            raise ValueError("excel3 failed")
        return pd.DataFrame()

    monkeypatch.setattr(processor, "_load_single_excel", raise_on_excel3)
    result = processor.load_excel_files(
        {"excel1": "mock1.xlsx", "excel2": "mock2.xlsx", "excel3": "mock3.xlsx", "excel4": "mock4.xlsx"}
    )
    assert result is False
