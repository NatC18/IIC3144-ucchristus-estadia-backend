import json
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from api.views import excel_import


@pytest.fixture
def rf():
    return RequestFactory()


# ===========================================================
# Helpers
# ===========================================================


def make_file(name="excel.xlsx", content=b"abc"):
    return SimpleUploadedFile(
        name,
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def make_files(valid=True):
    ext = "xlsx" if valid else "txt"
    return {
        "excel1": make_file(f"excel1.{ext}"),
        "excel2": make_file("excel2.xlsx"),
        "excel3": make_file("excel3.xlsx"),
        "excel4": make_file("excel4.xlsx"),
    }


# ===========================================================
# upload_excel_files
# ===========================================================


def test_upload_excel_files_missing_file(rf):
    files = {"excel1": make_file("excel1.xlsx")}
    request = rf.post("/upload", data=files)
    response = excel_import.upload_excel_files(request)
    data = json.loads(response.content)
    assert response.status_code == 400
    assert "Falta el archivo" in data["error"]


def test_upload_excel_files_invalid_format(rf):
    files = make_files(valid=False)
    request = rf.post("/upload", data=files)
    response = excel_import.upload_excel_files(request)
    data = json.loads(response.content)
    assert response.status_code == 400
    assert "Formato inválido" in data["error"]


@patch("api.views.excel_import.call_command")
def test_upload_excel_files_success(mock_call, rf):
    files = make_files()
    request = rf.post("/upload", data=files)
    mock_call.return_value = None
    response = excel_import.upload_excel_files(request)
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["success"] is True
    assert set(data["data"]["files_processed"]) == {"excel1", "excel2", "excel3", "excel4"}


@patch("api.views.excel_import.call_command", side_effect=Exception("fallo"))
@patch("api.views.excel_import.logger")
def test_upload_excel_files_import_command_fails(mock_logger, mock_call, rf):
    files = make_files()
    request = rf.post("/upload", data=files)
    response = excel_import.upload_excel_files(request)
    data = json.loads(response.content)
    assert response.status_code == 500
    assert not data["success"]
    mock_logger.error.assert_called()


@patch(
    "api.views.excel_import.shutil.rmtree", side_effect=Exception("permiso denegado")
)
@patch("api.views.excel_import.call_command")
@patch("api.views.excel_import.logger")
def test_upload_excel_files_cleanup_warns(mock_logger, mock_call, mock_rmtree, rf):
    files = make_files()
    request = rf.post("/upload", data=files)
    excel_import.upload_excel_files(request)
    mock_logger.warning.assert_called()


@patch("api.views.excel_import.logger")
def test_upload_excel_files_outer_exception(mock_logger, rf):
    """Rompe request.FILES"""

    class BrokenFILES(dict):
        def __contains__(self, key):
            raise Exception("boom")

    request = rf.post("/upload", data={})
    request._files = BrokenFILES()
    response = excel_import.upload_excel_files(request)
    data = json.loads(response.content)
    assert response.status_code == 500
    assert "Error interno" in data["error"]
    mock_logger.error.assert_called()


# ===========================================================
# import_status
# ===========================================================


def make_dummy_model():
    obj = types.SimpleNamespace()
    obj.objects = MagicMock()
    obj.objects.count.return_value = 5
    return obj


def test_import_status_success(monkeypatch, rf):
    sys.modules["api.models"] = types.SimpleNamespace(
        Paciente=make_dummy_model(),
        Episodio=make_dummy_model(),
        Gestion=make_dummy_model(),
    )
    request = rf.get("/status")
    response = excel_import.import_status(request)
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["success"]
    assert data["data"]["pacientes"] == 5


@patch("api.views.excel_import.logger")
def test_import_status_exception(mock_logger, rf):
    bad_model = types.SimpleNamespace()
    bad_model.objects = MagicMock()
    bad_model.objects.count.side_effect = Exception("db fail")
    sys.modules["api.models"] = types.SimpleNamespace(
        Paciente=bad_model,
        Episodio=bad_model,
        Gestion=bad_model,
    )
    request = rf.get("/status")
    response = excel_import.import_status(request)
    data = json.loads(response.content)
    assert response.status_code == 500
    assert not data["success"]
    mock_logger.error.assert_called()
