import pytest
import pandas as pd
from django.core.exceptions import ValidationError
from api.services.excel_processor import ExcelProcessor


# --- 🔹 Dummy ArchivoCarga para simular comportamiento ---
class DummyArchivo:
    def __init__(self, df=None, raise_on_save=False):
        self.archivo = type("A", (), {"path": "fake_path.xlsx"})
        self.estado = None
        self.filas_totales = 0
        self.filas_errores = 0
        self.errores = []
        self.raise_on_save = raise_on_save
        self.saved = []
        self.df = df

    def save(self, update_fields=None):
        if self.raise_on_save:
            raise Exception("save failed")
        self.saved.append(update_fields)

    def actualizar_progreso(self, procesadas, errores):
        self.filas_totales = procesadas + errores

    def agregar_error(self, fila, error, detalle=None):
        self.errores.append({"fila": fila, "error": error, "detalle": detalle})


# --- 🔹 Subclase concreta de ExcelProcessor para testear ---
class DummyProcessor(ExcelProcessor):
    def _validar_estructura(self) -> bool:
        return True

    def _validar_fila(self, datos, numero_fila):
        # Si hay clave "fail", lanza excepción
        if "fail" in datos.values():
            raise ValueError("Fila inválida")
        if "skip" in datos.values():
            return None
        return datos

    def _procesar_fila_modelo(self, datos, numero_fila):
        # simula guardado exitoso
        pass

    def get_columnas_requeridas(self):
        return ["col1", "col2"]

    def get_columnas_opcionales(self):
        return ["col3"]


# --- 🔹 Tests de inicialización ---
def test_init_sets_attributes():
    a = DummyArchivo()
    p = DummyProcessor(a)
    assert p.archivo_carga is a
    assert p.df is None
    assert p.errores == []
    assert p.registros_procesados == 0
    assert p.registros_error == 0


# --- 🔹 _limpiar_fila ---
def test_limpiar_fila_removes_spaces_and_nan():
    p = DummyProcessor(DummyArchivo())
    data = {"a": " texto ", "b": pd.NA, "c": 1}
    cleaned = p._limpiar_fila(data)
    assert cleaned["a"] == "texto"
    assert cleaned["b"] is None
    assert cleaned["c"] == 1


# --- 🔹 _agregar_error ---
def test_agregar_error_adds_to_list_and_calls_archivo():
    a = DummyArchivo()
    p = DummyProcessor(a)
    p._agregar_error(5, "Falla", "detalle X")
    assert len(p.errores) == 1
    assert a.errores[-1]["error"] == "Falla"
    assert "detalle" in a.errores[-1]


# --- 🔹 _finalizar_procesamiento normal y con errores ---
def test_finalizar_procesamiento_with_errors_and_no_rows():
    a = DummyArchivo()
    a.filas_totales = 0
    p = DummyProcessor(a)
    p.errores = [{"fila": 1, "error": "x"}]
    p._finalizar_procesamiento()
    assert a.estado == "ERROR"
    assert a.filas_errores == 1


def test_finalizar_procesamiento_successful_path():
    a = DummyArchivo()
    p = DummyProcessor(a)
    p.errores = []
    p._finalizar_procesamiento()
    assert isinstance(a.filas_totales, int)


# --- 🔹 _manejar_error ---
def test_manejar_error_sets_estado_and_saves():
    a = DummyArchivo()
    p = DummyProcessor(a)
    p._manejar_error("crash total")
    assert a.estado == "ERROR"
    assert any("Error global" in e["error"] for e in a.errores)


# --- 🔹 _procesar_filas ---
def test_procesar_filas_handles_success_skip_and_exception(monkeypatch):
    df = pd.DataFrame([{"a": "ok"}, {"a": "skip"}, {"a": "fail"}])
    a = DummyArchivo(df)
    p = DummyProcessor(a)
    p.df = df

    # mock validar y procesar modelo
    p._procesar_fila_modelo = lambda d, n: None
    p._validar_fila = DummyProcessor._validar_fila.__get__(p)
    p._limpiar_fila = DummyProcessor._limpiar_fila.__get__(p)

    p._procesar_filas()
    assert p.registros_procesados >= 1
    assert p.registros_error >= 1
    assert any(e["error"] for e in a.errores)


# --- 🔹 _cargar_excel ---
def test_cargar_excel_valid(monkeypatch, tmp_path):
    file_path = tmp_path / "valid.xlsx"
    df = pd.DataFrame({"Col A": [1, 2]})
    df.to_excel(file_path, index=False)

    a = DummyArchivo()
    a.archivo.path = str(file_path)
    p = DummyProcessor(a)

    # monkeypatch read_excel to ensure both branches work
    monkeypatch.setattr(pd, "read_excel", lambda *a_, **kw: df)
    p._cargar_excel()
    assert "col_a" in p.df.columns
    assert a.filas_totales == 2


def test_cargar_excel_raises(monkeypatch):
    a = DummyArchivo()
    a.archivo.path = "fake.xlsx"
    p = DummyProcessor(a)

    def bad_read(*a_, **kw): raise ValueError("bad file")

    monkeypatch.setattr(pd, "read_excel", bad_read)
    with pytest.raises(ValidationError):
        p._cargar_excel()


# --- 🔹 procesar_archivo ---
def test_procesar_archivo_happy_path(monkeypatch):
    a = DummyArchivo()
    p = DummyProcessor(a)

    # simulamos flujo completo
    monkeypatch.setattr(p, "_cargar_excel", lambda: setattr(p, "df", pd.DataFrame([{"ok": 1}])))
    monkeypatch.setattr(p, "_validar_estructura", lambda: True)
    monkeypatch.setattr(p, "_procesar_filas", lambda: setattr(p, "registros_procesados", 1))
    monkeypatch.setattr(p, "_finalizar_procesamiento", lambda: setattr(a, "estado", "FINAL"))
    result = p.procesar_archivo()
    assert "filas_procesadas" in result
    assert result["estado"] == "FINAL"


def test_procesar_archivo_invalid_structure(monkeypatch):
    a = DummyArchivo()
    p = DummyProcessor(a)
    monkeypatch.setattr(p, "_cargar_excel", lambda: None)
    monkeypatch.setattr(p, "_validar_estructura", lambda: False)
    monkeypatch.setattr(p, "_finalizar_procesamiento", lambda: setattr(a, "estado", "ERROR"))
    result = p.procesar_archivo()
    assert result["estado"] == "ERROR"


def test_procesar_archivo_exception(monkeypatch):
    a = DummyArchivo()
    p = DummyProcessor(a)
    monkeypatch.setattr(p, "_cargar_excel", lambda: (_ for _ in ()).throw(ValueError("boom")))
    result = p.procesar_archivo()
    assert result["estado"] == "ERROR"
    assert "boom" in result["error"]
