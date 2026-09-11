from unittest.mock import MagicMock, patch

from backend.integrations.ollama_client import generate_text


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
