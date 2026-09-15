from fastapi import APIRouter, HTTPException

from backend.db.database import (
    approve_triage_request,
    correct_triage_request,
    list_dispatches,
    update_dispatch_status,
)
from backend.modules.review.schemas import (
    DispatchRecord,
    DispatchStatusUpdate,
    ReviewCorrection,
    ReviewRecord,
)
from backend.modules.review.services import (
    get_review_record,
    list_completed_review_records,
    list_pending_review_records,
)
from backend.modules.review.dispatch import dispatch_reviewed_request


router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/dispatches", response_model=list[DispatchRecord])
def get_dispatches() -> list[DispatchRecord]:
    """Devuelve las solicitudes de las bandejas internas."""

    return [
        DispatchRecord(**dispatch)
        for dispatch in list_dispatches()
    ]


@router.put(
    "/dispatches/{dispatch_id}/status",
    response_model=DispatchRecord,
)
def change_dispatch_status(
    dispatch_id: int,
    update: DispatchStatusUpdate,
) -> DispatchRecord:
    """Cambia el estado de una solicitud derivada."""

    was_updated = update_dispatch_status(
        dispatch_id=dispatch_id,
        status=update.status,
    )

    if not was_updated:
        raise HTTPException(
            status_code=404,
            detail="Dispatch not found.",
        )

    updated_dispatch = next(
        (
            dispatch
            for dispatch in list_dispatches()
            if dispatch["id"] == dispatch_id
        ),
        None,
    )

    if updated_dispatch is None:
        raise HTTPException(
            status_code=500,
            detail="Updated dispatch could not be loaded.",
        )

    return DispatchRecord(**updated_dispatch)


@router.get("/pending", response_model=list[ReviewRecord])
def get_pending_reviews() -> list[ReviewRecord]:
    # Devolvemos la cola de propuestas pendientes de revisión humana.
    return list_pending_review_records()


@router.get("/completed", response_model=list[ReviewRecord])
def get_completed_reviews() -> list[ReviewRecord]:
    """Devuelve el histórico de solicitudes revisadas."""

    return list_completed_review_records()


@router.get("/{request_id}", response_model=ReviewRecord)
def get_review(request_id: int) -> ReviewRecord:
    record = get_review_record(request_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Review request not found.",
        )

    return record


@router.post("/{request_id}/approve", response_model=ReviewRecord)
def approve_review(request_id: int) -> ReviewRecord:
    record = get_review_record(request_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Review request not found.",
        )

    if record.review_status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Review request has already been completed.",
        )

    was_approved = approve_triage_request(request_id)

    if not was_approved:
        raise HTTPException(
            status_code=409,
            detail="Review request could not be approved.",
        )

    updated_record = get_review_record(request_id)

    if updated_record is None:
        raise HTTPException(
            status_code=500,
            detail="Approved review request could not be loaded.",
        )
    dispatch_reviewed_request(updated_record)

    return updated_record


@router.put("/{request_id}/correct", response_model=ReviewRecord)
def correct_review(
    request_id: int,
    correction: ReviewCorrection,
) -> ReviewRecord:
    record = get_review_record(request_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Review request not found.",
        )

    if record.review_status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Review request has already been completed.",
        )

    was_corrected = correct_triage_request(
        request_id,
        correction,
    )

    if not was_corrected:
        raise HTTPException(
            status_code=409,
            detail="Review request could not be corrected.",
        )

    updated_record = get_review_record(request_id)

    if updated_record is None:
        raise HTTPException(
            status_code=500,
            detail="Corrected review request could not be loaded.",
        )
    dispatch_reviewed_request(updated_record)

    return updated_record