from unittest.mock import MagicMock, patch

import pytest
from django.db import OperationalError
from django.test import RequestFactory
from django.urls import resolve

from config.health import health


def test_health_returns_200_on_successful_probe():
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)
    with patch("config.health.connection") as database:
        database.cursor.return_value.__enter__.return_value = cursor
        response = health(RequestFactory().get("/health/"))
    assert response.status_code == 200
    assert response.content == b'{"status": "ok"}'
    assert response["Cache-Control"] == "no-store"
    cursor.execute.assert_called_once_with("SELECT 1")


def test_health_hides_database_error():
    with patch("config.health.connection") as database:
        database.cursor.side_effect = OperationalError("private-password internal-host")
        response = health(RequestFactory().get("/health/"))
    assert response.status_code == 503
    assert response.content == b'{"status": "unavailable"}'
    assert b"private" not in response.content
    assert response["Cache-Control"] == "no-store"


def test_health_handles_unexpected_probe_result():
    with patch("config.health.connection") as database:
        database.cursor.return_value.__enter__.return_value.fetchone.return_value = None
        response = health(RequestFactory().get("/health/"))
    assert response.status_code == 503


def test_health_does_not_accept_mutations():
    with patch("config.health.connection") as database:
        response = health(RequestFactory().post("/health/"))
    assert response.status_code == 405
    database.cursor.assert_not_called()


def test_health_route_resolves_and_admin_is_not_exposed(client):
    assert resolve("/health/").func is health
    assert client.get("/admin/").status_code == 404


def test_unlisted_host_is_rejected(client):
    assert client.get("/health/", HTTP_HOST="attacker.invalid").status_code == 400


@pytest.mark.postgres
@pytest.mark.django_db
def test_health_queries_real_postgresql(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
