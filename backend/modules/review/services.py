from backend.db.database import (
    get_triage_request,
    list_pending_requests,
)
from backend.modules.review.schemas import (
    ReviewCorrection,
    ReviewRecord,
)
from backend.modules.triage.schemas import (
    TriageMetrics,
    TriageResponse,
)


def build_review_record(row: dict) -> ReviewRecord:
    # Reconstruimos la propuesta original del LLM.
    proposal = TriageResponse(
        category=row["llm_category"],
        urgency=row["llm_urgency"],
        responsible_party=row["llm_responsible_party"],
        summary=row["llm_summary"],
        department=row["llm_department"],
    )

    # Agrupamos las métricas almacenadas en la base de datos.
    metrics = TriageMetrics(
        provider=row["provider"],
        model=row["model"],
        attempts=row["attempts"],
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        latency_ms=row["latency_ms"],
        estimated_cost_usd=row["estimated_cost_usd"],
    )

    final_decision = None

    # Los campos finales solo existen después de una revisión.
    if row["final_category"] is not None:
        final_decision = ReviewCorrection(
            category=row["final_category"],
            urgency=row["final_urgency"],
            responsible_party=row["final_responsible_party"],
            summary=row["final_summary"],
            department=row["final_department"],
            review_notes=row["review_notes"],
        )

    return ReviewRecord(
        request_id=row["id"],
        message=row["message"],
        user_role=row["user_role"],
        proposal=proposal,
        metrics=metrics,
        review_status=row["review_status"],
        final_decision=final_decision,
        created_at=row["created_at"],
        reviewed_at=row["reviewed_at"],
    )


def get_review_record(request_id: int) -> ReviewRecord | None:
    row = get_triage_request(request_id)

    if row is None:
        return None

    return build_review_record(row)


def list_pending_review_records() -> list[ReviewRecord]:
    rows = list_pending_requests()

    return [build_review_record(row) for row in rows]