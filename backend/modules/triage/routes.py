from fastapi import APIRouter

from backend.modules.triage.schemas import TriageRequest

# Agrupamos las rutas relacionadas con el triaje.
router = APIRouter(prefix="/triage", tags=["Triage"])


# Recibimos y devolvemos los datos para comprobar su validación.
@router.post("/", response_model=TriageRequest)
def submit_request(request: TriageRequest):
    return request