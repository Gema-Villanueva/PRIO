from unittest.mock import MagicMock, patch

from backend.integrations.ollama_client import generate_text
from backend.integrations.external_client import (
    calculate_external_cost,
    calculate_retry_delay,
    generate_external_text,
)
from backend.config import settings


# Comprobamos que el cliente recoge tokens, tiempo y opciones de generación.
def test_ollama_client_returns_generation_metrics():
    provider_response = MagicMock()
    provider_response.json.return_value = {
        "response": '{"category": "general"}',
        "prompt_eval_count": 120,
        "eval_count": 18,
    }

    client = MagicMock()
    client.post.return_value = provider_response
    client_context = MagicMock()
    client_context.__enter__.return_value = client

    schema = {"type": "object"}
    with (
        patch("backend.integrations.ollama_client.httpx.Client", return_value=client_context),
        patch(
            "backend.integrations.ollama_client.perf_counter",
            side_effect=[10.0, 10.125],
        ),
    ):
        result = generate_text("request", "system", schema)

    sent_payload = client.post.call_args.kwargs["json"]
    assert sent_payload["options"] == {"temperature": 0}
    assert sent_payload["format"] == schema
    assert result.input_tokens == 120
    assert result.output_tokens == 18
    assert result.latency_ms == 125.0
    assert result.estimated_cost_usd == 0.0

# Comprobamos que el proveedor gratuito no genera coste por tokens.
def test_external_free_provider_has_zero_cost():
    cost = calculate_external_cost(
        input_tokens=1_000,
        output_tokens=100,
    )

    assert cost == 0.0

# Comprobamos que el cliente externo recoge la respuesta y sus métricas.
def test_external_client_returns_generation_metrics():
    provider_response = MagicMock()
    provider_response.status_code = 200
    provider_response.json.return_value = {
        "model": "openai/gpt-oss-20b",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": '{"category": "general"}',
                    }
                ],
            }
        ],
        "usage": {
            "input_tokens": 1_000,
            "output_tokens": 100,
        },
    }

    client = MagicMock()
    client.post.return_value = provider_response

    client_context = MagicMock()
    client_context.__enter__.return_value = client

    schema = {"type": "object"}

    with (
        patch(
            "backend.integrations.external_client.httpx.Client",
            return_value=client_context,
        ),
        patch(
            "backend.integrations.external_client.perf_counter",
            side_effect=[10.0, 10.5],
        ),
        patch.object(settings, "external_api_key", "test-key"),
    ):
        result = generate_external_text(
            "request",
            "system",
            schema,
        )

    sent_request = client.post.call_args

    assert sent_request.args[0] == (
        "https://api.groq.com/openai/v1/responses"
    )
    assert sent_request.kwargs["headers"]["Authorization"] == (
        "Bearer test-key"
    )
    assert sent_request.kwargs["json"]["model"] == (
        "openai/gpt-oss-20b"
    )
    assert result.text == '{"category": "general"}'
    assert result.input_tokens == 1_000
    assert result.output_tokens == 100
    assert result.latency_ms == 500.0
    assert result.provider == "groq"
    assert result.estimated_cost_usd == 0.0

# Comprobamos que el cliente reintenta una petición limitada por Groq.
def test_external_client_retries_after_rate_limit():
    rate_limit_response = MagicMock()
    rate_limit_response.status_code = 429
    rate_limit_response.headers = {}

    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {
        "model": "openai/gpt-oss-20b",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": '{"category": "general"}',
                    }
                ],
            }
        ],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 20,
        },
    }

    client = MagicMock()
    client.post.side_effect = [
        rate_limit_response,
        success_response,
    ]

    client_context = MagicMock()
    client_context.__enter__.return_value = client

    with (
        patch(
            "backend.integrations.external_client.httpx.Client",
            return_value=client_context,
        ),
        patch(
            "backend.integrations.external_client.perf_counter",
            side_effect=[10.0, 11.0],
        ),
        patch(
            "backend.integrations.external_client.sleep",
        ) as mocked_sleep,
        patch.object(settings, "external_api_key", "test-key"),
    ):
        result = generate_external_text("request")

    assert client.post.call_count == 2
    mocked_sleep.assert_called_once_with(1)
    assert result.provider == "groq"
    assert result.estimated_cost_usd == 0.0


# Respetamos la espera solicitada por el proveedor externo.
def test_external_retry_uses_retry_after_header():
    response = MagicMock()
    response.headers = {"retry-after": "12.5"}

    assert calculate_retry_delay(response, attempt=0) == 12.5
