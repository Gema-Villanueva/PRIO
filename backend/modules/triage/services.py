import json
from pathlib import Path
from pydantic import ValidationError

from backend.modules.triage.schemas import (
    TriageMetrics,
    TriageRequest,
    TriageResponse,
    TriageResult,
)
from backend.integrations.ollama_client import GenerationResult, generate_text


# Construimos la ruta al archivo que contiene las instrucciones del modelo.
# __file__ es este archivo (services.py) y resolve() obtiene su ruta completa.
# parents[2] sube hasta backend: triage → modules → backend.
PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"              # Entramos en la carpeta prompts.
    / "triage_system.txt"    # Seleccionamos el archivo de instrucciones.
)


def load_triage_prompt() -> str:
    # Leemos el archivo y devolvemos su contenido como texto.
    # UTF-8 permite interpretar correctamente tildes y otros caracteres.
    return PROMPT_PATH.read_text(encoding="utf-8")

def build_request_prompt(request: TriageRequest) -> str:
    # Convertimos la solicitud validada en un diccionario de Python.
    request_data = request.model_dump()

    # Lo convertimos en texto JSON para enviarlo al modelo.
    # Conservamos las tildes y usamos sangría para facilitar su lectura.
    return json.dumps(request_data, ensure_ascii=False, indent=2)


def build_triage_result(
    response: TriageResponse,
    generations: list[GenerationResult],
) -> TriageResult:
    # Sumamos también los tokens y el tiempo empleados en una corrección.
    metrics = TriageMetrics(
        provider=generations[-1].provider,
        model=generations[-1].model,
        attempts=len(generations),
        input_tokens=sum(item.input_tokens for item in generations),
        output_tokens=sum(item.output_tokens for item in generations),
        latency_ms=round(sum(item.latency_ms for item in generations), 2),
        estimated_cost_usd=round(
            sum(item.estimated_cost_usd for item in generations), 8
        ),
    )
    return TriageResult(**response.model_dump(), metrics=metrics)


def classify_request(request: TriageRequest) -> TriageResult:
    # Cargamos las instrucciones y los datos de la solicitud.
    system_prompt = load_triage_prompt()
    request_prompt = build_request_prompt(request)
    response_schema = TriageResponse.model_json_schema()

    first_generation = generate_text(
        prompt=request_prompt,
        system_prompt=system_prompt,
        response_schema=response_schema,
    )
    generations = [first_generation]

    try:
        # Comprobamos el formato y las reglas de la primera respuesta.
        response = TriageResponse.model_validate_json(first_generation.text)
        return build_triage_result(response, generations)

    except ValidationError as error:
        # Indicamos al modelo qué falló y le pedimos corregir su respuesta.
        correction_prompt = (
            f"Original request:\n{request_prompt}\n\n"
            f"Previous response:\n{first_generation.text}\n\n"
            f"Validation errors:\n{error}\n\n"
            "Correct the response to satisfy all validation rules. "
            "Keep it faithful to the original request. "
            "Return only the corrected JSON object."
        )

        corrected_generation = generate_text(
            prompt=correction_prompt,
            system_prompt=system_prompt,
            response_schema=response_schema,
        )
        generations.append(corrected_generation)

        # Validamos de nuevo. Si falla, propagamos el error:
        # no hacemos más intentos dentro de esta función.
        response = TriageResponse.model_validate_json(corrected_generation.text)
        return build_triage_result(response, generations)
