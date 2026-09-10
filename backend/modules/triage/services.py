import json
from pathlib import Path
from pydantic import ValidationError

from backend.modules.triage.schemas import TriageRequest, TriageResponse   
from backend.integrations.ollama_client import generate_text


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


def classify_request(request: TriageRequest) -> TriageResponse:
    # Cargamos las instrucciones y los datos de la solicitud.
    system_prompt = load_triage_prompt()
    request_prompt = build_request_prompt(request)

    raw_response = generate_text(
        prompt=request_prompt,
        system_prompt=system_prompt,
    )

    try:
        # Comprobamos el formato y las reglas de la primera respuesta.
        return TriageResponse.model_validate_json(raw_response)

    except ValidationError as error:
        # Indicamos al modelo qué falló y le pedimos corregir su respuesta.
        correction_prompt = (
            f"Original request:\n{request_prompt}\n\n"
            f"Previous response:\n{raw_response}\n\n"
            f"Validation errors:\n{error}\n\n"
            "Correct the response to satisfy all validation rules. "
            "Keep it faithful to the original request. "
            "Return only the corrected JSON object."
        )

        corrected_response = generate_text(
            prompt=correction_prompt,
            system_prompt=system_prompt,
        )

        # Mostramos la respuesta completa para diagnosticar esta prueba.
        print("Corrected model response:", corrected_response)

        # Validamos de nuevo. Si falla, propagamos el error:
        # no hacemos más intentos dentro de esta función.
        return TriageResponse.model_validate_json(corrected_response)