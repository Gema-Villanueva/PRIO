import httpx

from backend.config import settings


def generate_text(prompt: str, system_prompt: str = "") -> str:
    # Construimos la dirección de la API local de Ollama.
    url = f"{settings.ollama_base_url}/api/generate"

    # Separamos las instrucciones generales de los datos de la solicitud.
    # stream=False permite recibir la respuesta completa de una vez.
    payload = {
        "model": settings.ollama_model,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
    }

    # Enviamos la petición y comprobamos si hay un error HTTP.
    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()

    # Extraemos el texto generado del JSON que devuelve Ollama.
    return response.json()["response"]