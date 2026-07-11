"""Endpoint del webhook (Fase 5). Drive/pipeline mockeados vía dependency_overrides."""

import pytest
from fastapi.testclient import TestClient

from app.main import (
    Settings,
    app,
    get_allowlist_checker,
    get_procesador,
    get_rate_limiter,
    get_settings,
)
from app.security import RateLimiter

SECRET = "s3cr3t"
HEADERS_OK = {"X-Stragia-Secret": SECRET}
BODY_OK = {"sheetId": "SHEET_OK", "nombre": "ACME"}


@pytest.fixture
def client():
    llamadas = []
    limiter = RateLimiter(max_solicitudes=100, ventana_seg=60)
    app.dependency_overrides[get_settings] = lambda: Settings(
        secret=SECRET, input_folder_id="F"
    )
    app.dependency_overrides[get_allowlist_checker] = lambda: (
        lambda sid: sid == "SHEET_OK"
    )
    app.dependency_overrides[get_procesador] = lambda: (
        lambda sheet_id, nombre, run_id: llamadas.append((sheet_id, nombre, run_id))
    )
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    yield TestClient(app), llamadas
    app.dependency_overrides.clear()


def test_202_y_agenda_el_procesamiento(client):
    c, llamadas = client
    r = c.post("/v1/diagnosticos", json=BODY_OK, headers=HEADERS_OK)

    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "accepted"
    assert body["runId"]
    # el background task corrió con el sheetId y el mismo runId
    assert llamadas == [("SHEET_OK", "ACME", body["runId"])]


def test_401_secreto_incorrecto(client):
    c, _ = client
    r = c.post("/v1/diagnosticos", json=BODY_OK, headers={"X-Stragia-Secret": "malo"})
    assert r.status_code == 401


def test_401_sin_secreto(client):
    c, _ = client
    r = c.post("/v1/diagnosticos", json=BODY_OK)
    assert r.status_code == 401


def test_403_sheet_no_autorizado(client):
    c, _ = client
    r = c.post(
        "/v1/diagnosticos", json={"sheetId": "OTRO", "nombre": "X"}, headers=HEADERS_OK
    )
    assert r.status_code == 403


def test_400_payload_malformado(client):
    c, _ = client
    r = c.post("/v1/diagnosticos", json={"nombre": "falta sheetId"}, headers=HEADERS_OK)
    assert r.status_code == 400


def test_429_rate_limit():
    limiter = RateLimiter(max_solicitudes=1, ventana_seg=60)
    app.dependency_overrides[get_settings] = lambda: Settings(
        secret=SECRET, input_folder_id="F"
    )
    app.dependency_overrides[get_allowlist_checker] = lambda: (lambda sid: True)
    app.dependency_overrides[get_procesador] = lambda: (lambda *a: None)
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    c = TestClient(app)

    r1 = c.post("/v1/diagnosticos", json=BODY_OK, headers=HEADERS_OK)
    r2 = c.post("/v1/diagnosticos", json=BODY_OK, headers=HEADERS_OK)
    app.dependency_overrides.clear()

    assert r1.status_code == 202
    assert r2.status_code == 429
