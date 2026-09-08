import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.main import app
from backend.modules.triage.schemas import TriageResponse

# Creamos un cliente para probar la API sin arrancar Uvicorn.
client = TestClient(app)


# Comprobamos que se eliminan los espacios exteriores.
def test_triage_trims_message():
    response = client.post(
        "/triage/",
        json={
            "message": "  No puedo entrar  ",
            "user_role": "guest",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "No puedo entrar"


# Comprobamos que un mensaje compuesto solo por espacios se rechaza.
def test_triage_rejects_whitespace_message():
    response = client.post(
        "/triage/",
        json={
            "message": "   ",
            "user_role": "guest",
        },
    )

    assert response.status_code == 422


# Comprobamos que se rechazan los roles no permitidos.
def test_triage_rejects_invalid_role():
    response = client.post(
        "/triage/",
        json={
            "message": "No puedo entrar",
            "user_role": "admin",
        },
    )

    assert response.status_code == 422


# Comprobamos que se acepta un resumen de exactamente diez palabras.
def test_triage_response_accepts_ten_word_summary():
    result = TriageResponse(
        category="access",
        urgency="high",
        summary="Huésped sin acceso al alojamiento porque el código no funciona",
        department="reservation_support",
    )

    assert result.summary == (
        "Huésped sin acceso al alojamiento porque el código no funciona"
    )


# Comprobamos que se rechaza un resumen que no tiene diez palabras.
def test_triage_response_rejects_short_summary():
    with pytest.raises(ValidationError):
        TriageResponse(
            category="access",
            urgency="high",
            summary="No puede entrar",
            department="reservation_support",
        )