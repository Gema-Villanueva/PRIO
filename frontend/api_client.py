import httpx

from backend.config import settings


# Tiempo máximo que esperará el frontend a que el modelo responda.
# Ollama puede tardar bastante más que una petición web normal.
REQUEST_TIMEOUT_SECONDS = 90.0


def check_api_health() -> bool:
    """Comprueba si el backend de FastAPI está funcionando."""

    try:
        # Consultamos el endpoint sencillo de estado del backend.
        response = httpx.get(
            f"{settings.api_base_url}/health",
            timeout=5.0,
        )

        # Devolvemos True solamente cuando FastAPI responde correctamente.
        return response.status_code == 200

    except httpx.HTTPError:
        # Si FastAPI está apagado o no hay conexión, devolvemos False.
        return False


def get_provider_configuration() -> dict:
    """Consulta el modo de proveedor configurado en FastAPI."""

    response = httpx.get(
        f"{settings.api_base_url}/triage/provider",
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()


def update_provider_configuration(
    mode: str,
) -> dict:
    """Cambia el modo de proveedor utilizado por la plataforma."""

    response = httpx.put(
        f"{settings.api_base_url}/triage/provider",
        json={"mode": mode},
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()


def submit_triage(
    message: str,
    user_role: str,
    provider: str,
) -> dict:
    """Envía una solicitud a PRIO y devuelve su clasificación."""

    # Enviamos al backend el mensaje, el rol y el proveedor seleccionado.
    response = httpx.post(
        f"{settings.api_base_url}/triage/",
        json={
            "message": message,
            "user_role": user_role,
            "provider": provider,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    # Si FastAPI devuelve un error, httpx genera una excepción.
    # La página de Streamlit podrá capturarla y mostrar un aviso.
    response.raise_for_status()

    # Convertimos la respuesta JSON de FastAPI en un diccionario de Python.
    return response.json()


def get_pending_reviews() -> list[dict]:
    """Obtiene las solicitudes pendientes de revisión humana."""

    response = httpx.get(
        f"{settings.api_base_url}/reviews/pending",
        timeout=10.0,
    )
    response.raise_for_status()

    return response.json()


def get_completed_reviews() -> list[dict]:
    """Obtiene el histórico de solicitudes ya revisadas."""

    response = httpx.get(
        f"{settings.api_base_url}/reviews/completed",
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()


def approve_review(request_id: int) -> dict:
    """Aprueba una propuesta del modelo sin modificarla."""

    # El identificador indica qué solicitud pendiente queremos aprobar.
    response = httpx.post(
        f"{settings.api_base_url}/reviews/{request_id}/approve",
        timeout=10.0,
    )
    response.raise_for_status()

    return response.json()


def correct_review(
    request_id: int,
    correction: dict,
) -> dict:
    """Guarda la clasificación corregida por una persona."""

    # Enviamos la decisión humana al endpoint de corrección.
    response = httpx.put(
        f"{settings.api_base_url}/reviews/{request_id}/correct",
        json=correction,
        timeout=10.0,
    )
    response.raise_for_status()

    return response.json()