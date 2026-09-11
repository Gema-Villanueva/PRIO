from fastapi import APIRouter, HTTPException

from backend.db.database import (
    approve_triage_request,
    correct_triage_request,
)
from backend.modules.review.schemas import (
    ReviewCorrection,
    ReviewRecord,
)
from backend.modules.review.services import (
    get_review_record,
    list_pending_review_records,
)


router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/pending", response_model=list[ReviewRecord])
def get_pending_reviews() -> list[ReviewRecord]:
    # Devolvemos la cola de propuestas pendientes de revisión humana.
    return list_pending_review_records()


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

    return updated_record