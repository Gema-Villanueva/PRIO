import pytest
import json
from fastapi.testclient import TestClient
from pydantic import ValidationError
from unittest.mock import patch 

from backend.main import app
from backend.modules.triage.schemas import TriageResponse, TriageRequest
from backend.modules.triage.services import classify_request 

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


# Comprobamos que se acepta un resumen dentro del intervalo permitido.
def test_triage_response_accepts_valid_summary():
    result = TriageResponse(
        category="access",
        urgency="high",
        responsible_party="platform",
        summary="Huésped sin acceso al alojamiento porque el código no funciona",
        department="reservation_support",
    )

    assert result.summary == (
        "Huésped sin acceso al alojamiento porque el código no funciona"
    )


# Comprobamos que el error informa del número de palabras recibido.
def test_triage_response_rejects_short_summary():
    with pytest.raises(
        ValidationError,
        match="Summary must contain between 5 and 25 words; received 3",
    ):
        TriageResponse(
            category="access",
            urgency="high",
            responsible_party="platform",
            summary="No puede entrar",
            department="reservation_support",
        )


# Simulamos una respuesta incorrecta seguida de una corrección válida.
def test_classify_request_corrects_invalid_summary():
    request = TriageRequest(
        message="El código de entrada no funciona.",
        user_role="guest",
    )

    invalid_response = {
        "category": "access",
        "urgency": "high",
        "responsible_party": "platform",
        "summary": "No puede entrar",
        "department": "reservation_support",
    }

    # Conservamos los demás campos y sustituimos el resumen.
    valid_response = {
        **invalid_response,
        "summary": "Huésped sin acceso al alojamiento porque el código no funciona",
    }

    # Sustituimos la llamada real por dos respuestas predeterminadas.
    with patch(
        "backend.modules.triage.services.generate_text",
        side_effect=[
            json.dumps(invalid_response),
            json.dumps(valid_response),
        ],
    ) as mock_generate:
        result = classify_request(request)

    assert result.summary == valid_response["summary"]
    assert mock_generate.call_count == 2

    # Verificamos que la segunda llamada recibe el recuento del error.
    correction_prompt = mock_generate.call_args.kwargs["prompt"]
    assert "received 3" in correction_prompt


# Comprobamos que dos respuestas inválidas agotan los intentos.
def test_classify_request_stops_after_two_invalid_responses():
    request = TriageRequest(
        message="El código de entrada no funciona.",
        user_role="guest",
    )

    invalid_response = {
        "category": "access",
        "urgency": "high",
        "responsible_party": "platform",
        "summary": "No puede entrar",
        "department": "reservation_support",
    }

    # Ambas llamadas devolverán el mismo resumen de tres palabras.
    with patch(
        "backend.modules.triage.services.generate_text",
        return_value=json.dumps(invalid_response),
    ) as mock_generate:
        with pytest.raises(ValidationError, match="received 3"):
            classify_request(request)

    assert mock_generate.call_count == 2

    # Comprobamos que ambos extremos del intervalo están permitidos.
@pytest.mark.parametrize("word_count", [5, 25])
def test_triage_response_accepts_summary_length_boundaries(word_count):
    summary = " ".join(["word"] * word_count)

    result = TriageResponse(
        category="general",
        urgency="low",
        responsible_party="host",
        summary=summary,
        department="general_support",
    )

    assert len(result.summary.split()) == word_count


# Comprobamos que se rechazan las longitudes fuera del intervalo.
@pytest.mark.parametrize("word_count", [4, 26])
def test_triage_response_rejects_summary_outside_limits(word_count):
    summary = " ".join(["word"] * word_count)

    with pytest.raises(ValidationError, match=f"received {word_count}"):
        TriageResponse(
            category="general",
            urgency="low",
            responsible_party="host",
            summary=summary,
            department="general_support",
        )