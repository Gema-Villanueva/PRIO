import httpx
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from backend.db.database import save_triage_request
from backend.modules.triage.provider_settings import (
    get_provider_mode,
    set_provider_mode,
)
from backend.modules.triage.schemas import (
    ProviderConfiguration,
    StoredTriageResult,
    TriageRequest,
)
from backend.modules.triage.services import classify_request


# Agrupamos las rutas relacionadas con el triaje.
router = APIRouter(prefix="/triage", tags=["Triage"])


@router.get(
    "/provider",
    response_model=ProviderConfiguration,
)
def get_provider_configuration() -> ProviderConfiguration:
    """Devuelve el modo de proveedor seleccionado por el equipo."""

    return ProviderConfiguration(
        mode=get_provider_mode(),
    )


@router.put(
    "/provider",
    response_model=ProviderConfiguration,
)
def update_provider_configuration(
    configuration: ProviderConfiguration,
) -> ProviderConfiguration:
    """Cambia el modo utilizado para las próximas solicitudes."""

    selected_mode = set_provider_mode(configuration.mode)

    return ProviderConfiguration(
        mode=selected_mode,
    )


@router.post("/", response_model=StoredTriageResult)
def submit_request(request: TriageRequest) -> StoredTriageResult:
    try:
        # Ejecutamos el triaje y guardamos su propuesta para revisión humana.
        result = classify_request(request)
        request_id = save_triage_request(request, result)

        return StoredTriageResult(
            **result.model_dump(),
            request_id=request_id,
        )

    except ValidationError as error:
        # El modelo no produjo una respuesta válida tras los dos intentos.
        raise HTTPException(
            status_code=502,
            detail="The model returned an invalid triage response.",
        ) from error

    except httpx.TimeoutException as error:
        # El proveedor ha superado el tiempo de espera configurado.
        raise HTTPException(
            status_code=504,
            detail="The model provider timed out.",
        ) from error

    except httpx.HTTPError as error:
        # Gestionamos errores de conexión o estados HTTP de fallo.
        raise HTTPException(
            status_code=502,
            detail="The model provider request failed.",
        ) from error
