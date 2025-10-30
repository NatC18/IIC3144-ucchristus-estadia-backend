import os
import io
import pytest
import pandas as pd
from django.core.management.base import CommandError
from api.management.commands.importar_excel_local import Command


@pytest.fixture
def command():
  """Crea una instancia del comando con stdout simulado."""
  cmd = Command()
  cmd.stdout = io.StringIO()
  return cmd


def test_get_folder_path_absolute(tmp_path, command):
  path = command._get_folder_path(str(tmp_path))
  assert path == str(tmp_path)


def test_get_folder_path_relative(tmp_path, settings, command):
  settings.BASE_DIR = tmp_path
  folder = tmp_path / "excel_files"
  folder.mkdir()
  result = command._get_folder_path("excel_files")
  assert result == str(folder)


def test_get_folder_path_not_exists(tmp_path, settings, command):
  settings.BASE_DIR = tmp_path
  with pytest.raises(CommandError):
    command._get_folder_path("no_folder")


def test_check_excel_files_found(tmp_path, command):
  # Crea tres archivos excel1.xlsx, excel2.xlsx, excel3.xlsx
  for i in range(1, 4):
    (tmp_path / f"excel{i}.xlsx").touch()

  files = command._check_excel_files(str(tmp_path))
  assert all(k in files for k in ["excel1", "excel2", "excel3"])


def test_check_excel_files_with_xls_extension(tmp_path, command):
  # Crea solo excel1.xls para probar fallback
  (tmp_path / "excel1.xls").touch()
  (tmp_path / "excel2.xlsx").touch()
  (tmp_path / "excel3.xlsx").touch()

  files = command._check_excel_files(str(tmp_path))
  assert "excel1" in files


def test_check_excel_files_missing(tmp_path, command):
  (tmp_path / "excel1.xlsx").touch()
  (tmp_path / "excel2.xlsx").touch()
  # Falta excel3
  with pytest.raises(CommandError):
    command._check_excel_files(str(tmp_path))


def test_list_excel_files_with_and_without_required(tmp_path, command):
  (tmp_path / "excel1.xlsx").write_text("data")
  (tmp_path / "otro.xlsx").write_text("x")
  command._list_excel_files(str(tmp_path))
  output = command.stdout.getvalue()
  assert "Archivos Excel encontrados" in output


def test_list_excel_files_empty(tmp_path, command):
  command._list_excel_files(str(tmp_path))
  output = command.stdout.getvalue()
  assert "No se encontraron archivos" in output


def test_simulate_import_basic_verbose1(command):
  """Debe imprimir conteo sin ejemplos (verbosity=1)"""
  command.verbosity = 1
  mapped_data = {
      "pacientes": [{"rut": "1", "nombre": "A"}],
      "episodios": [{"episodio_cmbd": "E1"}],
      "gestiones": [{"fecha_ingreso": "2024-01-01"}],
  }
  command._simulate_import(mapped_data)
  output = command.stdout.getvalue()
  assert "Pacientes" in output and "Modo DRY-RUN" in output


def test_simulate_import_verbose2(command):
  """Debe incluir ejemplos de registros si verbosity=2"""
  command.verbosity = 2
  mapped_data = {
      "pacientes": [{"rut": "123", "nombre": "Felipe"}],
      "episodios": [{"episodio_cmbd": "EP1"}],
      "gestiones": [{"fecha_ingreso": "2024-05-01"}],
  }
  command._simulate_import(mapped_data)
  output = command.stdout.getvalue()
  assert "Ejemplo" in output


def test_show_import_results_with_errors(command):
  results = {
      "pacientes": {"created": 1, "updated": 0, "errors": 1},
      "episodios": {"created": 0, "updated": 1, "errors": 2},
      "gestiones": {"created": 0, "updated": 0, "errors": 0},
      "errors": ["Error A", "Error B"]
  }
  command._show_import_results(results)
  output = command.stdout.getvalue()
  assert "Errores" in output and "Total" in output


def test_show_import_results_without_errors(command):
  results = {
      "pacientes": {"created": 2, "updated": 1, "errors": 0},
      "episodios": {"created": 0, "updated": 0, "errors": 0},
      "gestiones": {"created": 1, "updated": 0, "errors": 0},
  }
  command._show_import_results(results)
  assert "Sin errores" in command.stdout.getvalue()


def test_handle_list_files(monkeypatch, tmp_path, command):
  """Cubre opción --list-files"""
  monkeypatch.setattr(command, "_get_folder_path", lambda x: str(tmp_path))
  monkeypatch.setattr(command, "_list_excel_files", lambda x: command.stdout.write("listed"))
  command.handle(folder=str(tmp_path), list_files=True, verbose=False, dry_run=False, export_combined=None)
  assert "listed" in command.stdout.getvalue()


def test_handle_dry_run(monkeypatch, tmp_path, command):
  """Simula flujo principal con dry-run"""
  # crear carpeta con excels
  for i in range(1, 4):
    (tmp_path / f"excel{i}.xlsx").touch()

  # mocks
  monkeypatch.setattr(command, "_get_folder_path", lambda x: str(tmp_path))
  monkeypatch.setattr(command, "_check_excel_files", lambda x: {"excel1": "a", "excel2": "b", "excel3": "c"})

  class DummyExcel:
    def process_local_files(self, files):
      return {"pacientes": pd.DataFrame([{"rut": "1"}]), "episodios": pd.DataFrame([{"episodio_cmbd": "EP1"}]), "gestiones": pd.DataFrame([{"fecha_ingreso": "2024"}])}

  class DummyMapper:
    def map_processed_data(self, data): return {"pacientes": [{}], "episodios": [{}], "gestiones": [{}]}

  monkeypatch.setattr("api.management.commands.importar_excel_local.ExcelProcessor", DummyExcel)
  monkeypatch.setattr("api.management.commands.importar_excel_local.DataMapper", DummyMapper)
  monkeypatch.setattr(command, "_simulate_import", lambda data: command.stdout.write("simulated"))

  command.handle(folder=str(tmp_path), list_files=False, verbose=True, dry_run=True, export_combined=None)
  assert "simulated" in command.stdout.getvalue()


def test_handle_export_combined(monkeypatch, tmp_path, command):
  """Cubre opción --export-combined"""
  export_path = tmp_path / "out.xlsx"
  dummy_df = pd.DataFrame([{"a": 1}])

  monkeypatch.setattr(command, "_get_folder_path", lambda x: str(tmp_path))
  monkeypatch.setattr(command, "_check_excel_files", lambda x: {"excel1": "a", "excel2": "b", "excel3": "c"})

  class DummyExcel:
    def process_local_files(self, files):
      return {"pacientes": dummy_df, "episodios": dummy_df, "gestiones": dummy_df}

  class DummyMapper:
    def map_processed_data(self, data): return {"pacientes": [], "episodios": [], "gestiones": []}

  class DummyDB:
    def import_data(self, data): return {"details": {"pacientes": {"created":1,"updated":0,"errors":0}, "episodios": {"created":0,"updated":1,"errors":0}, "gestiones": {"created":0,"updated":0,"errors":0}}}

  monkeypatch.setattr("api.management.commands.importar_excel_local.ExcelProcessor", DummyExcel)
  monkeypatch.setattr("api.management.commands.importar_excel_local.DataMapper", DummyMapper)
  monkeypatch.setattr("api.management.commands.importar_excel_local.DatabaseImporter", DummyDB)

  command.handle(folder=str(tmp_path), list_files=False, verbose=False, dry_run=False, export_combined=str(export_path))
  assert export_path.exists()


def test_handle_with_exception(monkeypatch, command):
  """Fuerza excepción general"""
  monkeypatch.setattr(command, "_get_folder_path", lambda x: (_ for _ in ()).throw(Exception("fail")))
  with pytest.raises(CommandError):
    command.handle(folder=".", list_files=False, verbose=False, dry_run=False, export_combined=None)
