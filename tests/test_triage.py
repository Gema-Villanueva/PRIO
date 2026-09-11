import pytest
import json
import httpx
from fastapi.testclient import TestClient
from pydantic import ValidationError
from unittest.mock import patch 

from backend.main import app
from backend.integrations.ollama_client import GenerationResult
from backend.modules.triage.schemas import (
    TriageMetrics,
    TriageRequest,
    TriageResponse,
    TriageResult,
)
from backend.modules.triage.services import classify_request 

# Creamos un cliente para probar la API sin arrancar Uvicorn.
client = TestClient(app)


def generation_result(text, input_tokens=10, output_tokens=5, latency_ms=20.0):
    return GenerationResult(
        text=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        provider="ollama",
        model="llama3.2:3b",
        estimated_cost_usd=0.0,
    )


# Comprobamos que la API limpia, clasifica y registra el mensaje.
def test_triage_trims_message():
    expected_result = TriageResult(
        category="access",
        urgency="high",
        responsible_party="platform",
        summary="El huésped no puede entrar al alojamiento.",
        department="reservation_support",
        metrics=TriageMetrics(
            provider="ollama",
            model="llama3.2:3b",
            attempts=1,
            input_tokens=10,
            output_tokens=5,
            latency_ms=20.0,
            estimated_cost_usd=0.0,
        ),
    )

    # Sustituimos el modelo y la base de datos por resultados controlados.
    with (
        patch(
            "backend.modules.triage.routes.classify_request",
            return_value=expected_result,
        ) as mock_classify,
        patch(
            "backend.modules.triage.routes.save_triage_request",
            return_value=42,
        ) as mock_save,
    ):
        response = client.post(
            "/triage/",
            json={
                "message": "  No puedo entrar  ",
                "user_role": "guest",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        **expected_result.model_dump(),
        "request_id": 42,
        "review_status": "pending",
    }

    # Verificamos que el servicio recibe el mensaje limpio.
    mock_classify.assert_called_once()
    received_request = mock_classify.call_args.args[0]
    assert received_request.message == "No puedo entrar"
    assert received_request.user_role == "guest"

    # Verificamos que se guarda la solicitud junto con su resultado.
    mock_save.assert_called_once_with(received_request, expected_result)


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
            generation_result(
                json.dumps(invalid_response),
                input_tokens=12,
                output_tokens=4,
                latency_ms=25.0,
            ),
            generation_result(
                json.dumps(valid_response),
                input_tokens=18,
                output_tokens=7,
                latency_ms=30.0,
            ),
        ],
    ) as mock_generate:
        result = classify_request(request)

    assert result.summary == valid_response["summary"]
    assert mock_generate.call_count == 2
    assert result.metrics.attempts == 2
    assert result.metrics.input_tokens == 30
    assert result.metrics.output_tokens == 11
    assert result.metrics.latency_ms == 55.0
    assert result.metrics.estimated_cost_usd == 0.0

    # Ambas llamadas deben pedir una respuesta estructurada al modelo.
    for model_call in mock_generate.call_args_list:
        assert model_call.kwargs["response_schema"] == (
            TriageResponse.model_json_schema()
        )

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
        return_value=generation_result(json.dumps(invalid_response)),
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
        department=None,
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
            department=None,
        )

# Comprobamos que un tiempo de espera agotado devuelve un error 504.
def test_triage_returns_504_when_provider_times_out():
    with patch(
        "backend.modules.triage.routes.classify_request",
        side_effect=httpx.ReadTimeout("Model response timed out"),
    ):
        response = client.post(
            "/triage/",
            json={
                "message": "No puedo entrar al alojamiento.",
                "user_role": "guest",
            },
        )

    assert response.status_code == 504
    assert response.json() == {
        "detail": "The model provider timed out."
    }

# Comprobamos que una respuesta inválida del modelo devuelve un error 502.
def test_triage_returns_502_when_model_response_is_invalid():
    def simulate_invalid_response(request):
        # El objeto vacío incumple el esquema y genera un error de Pydantic.
        return TriageResponse.model_validate({})

    with patch(
        "backend.modules.triage.routes.classify_request",
        side_effect=simulate_invalid_response,
    ):
        response = client.post(
            "/triage/",
            json={
                "message": "No puedo entrar al alojamiento.",
                "user_role": "guest",
            },
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The model returned an invalid triage response."
    }

    # Comprobamos que un fallo de conexión con el proveedor devuelve un 502.
def test_triage_returns_502_when_provider_connection_fails():
    with patch(
        "backend.modules.triage.routes.classify_request",
        side_effect=httpx.ConnectError("Could not connect to provider"),
    ):
        response = client.post(
            "/triage/",
            json={
                "message": "No puedo entrar al alojamiento.",
                "user_role": "guest",
            },
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The model provider request failed."
    }

# Rechazamos combinaciones incompatibles de destinatario y departamento.
@pytest.mark.parametrize(
    "responsible_party, department, expected_error",
    [
        (
            "host",
            "general_support",
            "Department must be null when responsible_party is host.",
        ),
        (
            "platform",
            None,
            "Department is required when responsible_party is platform.",
        ),
    ],
)
def test_triage_response_rejects_invalid_department_assignment(
    responsible_party, department, expected_error
):
    with pytest.raises(ValidationError) as error_info:
        TriageResponse(
            category="general",
            urgency="low",
            responsible_party=responsible_party,
            summary="El huésped solicita información sobre el alojamiento.",
            department=department,
        )

    assert expected_error in str(error_info.value)


# Rechazamos decisiones que contradicen reglas inequívocas del negocio.
@pytest.mark.parametrize(
    "response_data, expected_error",
    [
        (
            {
                "category": "booking",
                "urgency": "high",
                "responsible_party": "host",
                "department": None,
            },
            "Category booking must be handled by platform.",
        ),
        (
            {
                "category": "safety",
                "urgency": "high",
                "responsible_party": "platform",
                "department": "trust_and_safety",
            },
            "Category safety must have critical urgency.",
        ),
        (
            {
                "category": "payment",
                "urgency": "medium",
                "responsible_party": "platform",
                "department": "general_support",
            },
            "Category payment must use department payments",
        ),
    ],
)
def test_triage_response_rejects_business_rule_conflicts(
    response_data, expected_error
):
    with pytest.raises(ValidationError, match=expected_error):
        TriageResponse(
            **response_data,
            summary="La solicitud necesita una clasificación coherente para su revisión.",
        )
