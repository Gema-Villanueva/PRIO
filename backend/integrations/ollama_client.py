from dataclasses import dataclass
from time import perf_counter

import httpx

from backend.config import settings


@dataclass(frozen=True)
class GenerationResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    provider: str
    model: str
    estimated_cost_usd: float


def generate_text(
    prompt: str,
    system_prompt: str = "",
    response_schema: dict | None = None,
) -> GenerationResult:
    # Construimos la dirección de la API local de Ollama.
    url = f"{settings.ollama_base_url}/api/generate"

    # Separamos las instrucciones generales de los datos de la solicitud.
    # stream=False permite recibir la respuesta completa de una vez.
    payload = {
        "model": settings.ollama_model,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
        # Reducimos la variación para obtener clasificaciones reproducibles.
        "options": {"temperature": 0},
    }

    # Ollama usa este esquema para generar directamente un objeto JSON válido.
    if response_schema is not None:
        payload["format"] = response_schema

    # Enviamos la petición y comprobamos si hay un error HTTP.
    started_at = perf_counter()
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
    finally:
        latency_ms = (perf_counter() - started_at) * 1000

    # Ollama devuelve el texto y los tokens reales utilizados por la llamada.
    response_data = response.json()
    return GenerationResult(
        text=response_data["response"],
        input_tokens=response_data.get("prompt_eval_count", 0),
        output_tokens=response_data.get("eval_count", 0),
        latency_ms=latency_ms,
        provider="ollama",
        model=settings.ollama_model,
        # Ollama se ejecuta localmente y no genera una factura por tokens.
        estimated_cost_usd=0.0,
    )
