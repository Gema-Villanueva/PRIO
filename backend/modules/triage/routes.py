import httpx
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from backend.modules.triage.schemas import StoredTriageResult, TriageRequest
from backend.modules.triage.services import classify_request
from backend.db.database import save_triage_request


# Agrupamos las rutas relacionadas con el triaje.
router = APIRouter(prefix="/triage", tags=["Triage"])


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
