from time import perf_counter, sleep

import httpx

from backend.config import settings
from backend.integrations.schemas import GenerationResult


MAX_ATTEMPTS = 3


def extract_output_text(response_data: dict) -> str:
    # Buscamos el texto generado dentro de la respuesta del proveedor externo.
    for output_item in response_data.get("output", []):
        if output_item.get("type") != "message":
            continue

        for content_item in output_item.get("content", []):
            if content_item.get("type") == "output_text":
                return content_item["text"]

    raise ValueError(
    "External provider response does not contain output text"
    )


def calculate_external_cost(
    input_tokens: int,
    output_tokens: int,
) -> float:
    # Los precios están expresados por cada millón de tokens.
    input_cost = (
        input_tokens
        * settings.external_input_cost_per_million
        / 1_000_000
    )
    output_cost = (
        output_tokens
        * settings.external_output_cost_per_million
        / 1_000_000
    )

    return input_cost + output_cost


def generate_external_text(
    prompt: str,
    system_prompt: str = "",
    response_schema: dict | None = None,
) -> GenerationResult:
    if not settings.external_api_key:
        raise RuntimeError("EXTERNAL_API_KEY is not configured")

    url = f"{settings.external_base_url}/responses"

    headers = {
        "Authorization": f"Bearer {settings.external_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.external_model,
        "instructions": system_prompt,
        "input": prompt,
        "store": False,
        "temperature": 0,
        "reasoning": {
            "effort": "low",
        },
        "max_output_tokens": 500,
    }

    # Pedimos que la respuesta cumpla el mismo esquema usado con Ollama.
    if response_schema is not None:
        payload["text"] = {
            "format": {
                "type": "json_schema",
                "name": "triage_response",
                "schema": response_schema,
                "strict": True,
            }
        }

    started_at = perf_counter()

    with httpx.Client(timeout=60.0) as client:
        for attempt in range(MAX_ATTEMPTS):
            response = client.post(
                url,
                headers=headers,
                json=payload,
            )

            # Reintentamos límites de uso y errores temporales del servidor.
            should_retry = (
                response.status_code == 429
                or response.status_code >= 500
            )

            if should_retry and attempt < MAX_ATTEMPTS - 1:
                sleep(2 ** attempt)
                continue

            response.raise_for_status()
            break

    latency_ms = (perf_counter() - started_at) * 1000
    response_data = response.json()
    usage = response_data.get("usage", {})

    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    return GenerationResult(
        text=extract_output_text(response_data),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        provider=settings.external_provider,
        model=response_data.get("model", settings.external_model),
        estimated_cost_usd=calculate_external_cost(
            input_tokens,
            output_tokens,
        ),
    )