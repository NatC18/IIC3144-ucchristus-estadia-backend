import json
from unittest.mock import MagicMock, patch

import pytest
from django.http import JsonResponse

from api.views.health import health_check


@pytest.mark.django_db
def test_health_check_ok(rf):
    """Debe retornar 200 y status 'healthy' cuando la DB responde correctamente"""
    request = rf.get("/health/")
    mock_cursor = MagicMock()

    with patch("api.views.health.connection.cursor") as mock_conn:
        mock_conn.return_value.__enter__.return_value = mock_cursor
        response = health_check(request)

    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "UC Christus Backend is running" in data["message"]


@pytest.mark.django_db
def test_health_check_db_error(rf):
    """Debe retornar 503 y status 'unhealthy' si ocurre un error en la conexión DB"""
    request = rf.get("/health/")

    with patch("api.views.health.connection.cursor", side_effect=Exception("DB error")):
        response = health_check(request)

    assert response.status_code == 503
    data = json.loads(response.content)
    assert data["status"] == "unhealthy"
    assert data["database"] == "disconnected"
    assert "error" in data
    assert "DB error" in data["error"]
