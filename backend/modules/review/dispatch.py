from backend.db.database import save_dispatch
from backend.modules.review.schemas import ReviewRecord


DEPARTMENT_NAMES = {
    "reservation_support": "Soporte de reservas",
    "payments": "Pagos y facturación",
    "property_support": "Soporte del alojamiento",
    "trust_and_safety": "Confianza y seguridad",
    "general_support": "Atención general",
}


def dispatch_reviewed_request(record: ReviewRecord) -> int:
    """Registra el destino de una solicitud después de su revisión."""

    # Utilizamos la decisión definitiva aprobada o corregida.
    decision = record.final_decision or record.proposal

    if decision.responsible_party == "host":
        dispatch_type = "host_notification"
        destination = "Anfitrión"
        message = (
            f"Nueva solicitud que requiere tu atención: "
            f"{decision.summary}"
        )
    else:
        dispatch_type = "department_assignment"
        destination = DEPARTMENT_NAMES[decision.department]
        message = (
            f"Nueva solicitud asignada a {destination}: "
            f"{decision.summary}"
        )

    return save_dispatch(
        request_id=record.request_id,
        dispatch_type=dispatch_type,
        destination=destination,
        message=message,
    )