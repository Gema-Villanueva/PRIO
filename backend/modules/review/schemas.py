from typing import Literal

from pydantic import BaseModel, Field

from backend.modules.triage.schemas import TriageMetrics, TriageResponse


# Datos que puede corregir una persona durante la revisión.
class ReviewCorrection(TriageResponse):
    review_notes: str | None = Field(
        default=None,
        max_length=1000,
    )


# Representación completa de una solicitud para la revisión humana.
class ReviewRecord(BaseModel):
    request_id: int = Field(ge=1)
    message: str
    user_role: Literal["guest", "host"]

    proposal: TriageResponse
    metrics: TriageMetrics

    review_status: Literal[
        "pending",
        "approved",
        "corrected",
    ]

    final_decision: ReviewCorrection | None = None

    created_at: str
    reviewed_at: str | None = None


# Representación de una solicitud derivada a una bandeja interna.
class DispatchRecord(BaseModel):
    id: int = Field(ge=1)
    request_id: int = Field(ge=1)
    dispatch_type: Literal[
        "host_notification",
        "department_assignment",
    ]
    destination: str
    message: str
    status: Literal[
        "new",
        "in_progress",
        "resolved",
    ]
    created_at: str

# Estado que puede seleccionarse desde una bandeja interna.
class DispatchStatusUpdate(BaseModel):
    status: Literal[
        "new",
        "in_progress",
        "resolved",
    ]