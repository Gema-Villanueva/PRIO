from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.modules.review.schemas import ReviewCorrection, ReviewRecord
from backend.modules.triage.schemas import TriageMetrics, TriageResponse


client = TestClient(app)


def create_pending_record() -> ReviewRecord:
    return ReviewRecord(
        request_id=1,
        message="Necesito cancelar una reserva.",
        user_role="guest",
        proposal=TriageResponse(
            category="booking",
            urgency="medium",
            responsible_party="platform",
            summary="El huésped solicita cancelar una reserva futura.",
            department="reservation_support",
        ),
        metrics=TriageMetrics(
            provider="ollama",
            model="llama3.2:3b",
            attempts=1,
            input_tokens=80,
            output_tokens=15,
            latency_ms=1200.0,
            estimated_cost_usd=0.0,
        ),
        review_status="pending",
        created_at="2026-09-11 12:00:00",
    )


# Comprobamos que la API devuelve la cola pendiente.
def test_get_pending_reviews():
    pending_record = create_pending_record()

    with patch(
        "backend.modules.review.routes.list_pending_review_records",
        return_value=[pending_record],
    ):
        response = client.get("/reviews/pending")

    assert response.status_code == 200
    assert response.json() == [pending_record.model_dump()]


# Comprobamos la respuesta cuando una solicitud no existe.
def test_get_review_returns_404_when_not_found():
    with patch(
        "backend.modules.review.routes.get_review_record",
        return_value=None,
    ):
        response = client.get("/reviews/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Review request not found.",
    }


# Comprobamos que una propuesta pendiente puede aprobarse.
def test_approve_review():
    pending_record = create_pending_record()

    approved_record = pending_record.model_copy(
        update={
            "review_status": "approved",
            "final_decision": ReviewCorrection(
                **pending_record.proposal.model_dump(),
            ),
            "reviewed_at": "2026-09-11 12:10:00",
        }
    )

    with (
        patch(
            "backend.modules.review.routes.get_review_record",
            side_effect=[pending_record, approved_record],
        ),
        patch(
            "backend.modules.review.routes.approve_triage_request",
            return_value=True,
        ) as mock_approve,
    ):
        response = client.post("/reviews/1/approve")

    assert response.status_code == 200
    assert response.json() == approved_record.model_dump()
    mock_approve.assert_called_once_with(1)


# Comprobamos que una persona puede corregir la propuesta.
def test_correct_review():
    pending_record = create_pending_record()

    correction_data = {
        "category": "booking",
        "urgency": "high",
        "responsible_party": "platform",
        "summary": "El huésped necesita cancelar una reserva con atención prioritaria.",
        "department": "reservation_support",
        "review_notes": "La llegada está próxima.",
    }

    correction = ReviewCorrection(**correction_data)

    corrected_record = pending_record.model_copy(
        update={
            "review_status": "corrected",
            "final_decision": correction,
            "reviewed_at": "2026-09-11 12:15:00",
        }
    )

    with (
        patch(
            "backend.modules.review.routes.get_review_record",
            side_effect=[pending_record, corrected_record],
        ),
        patch(
            "backend.modules.review.routes.correct_triage_request",
            return_value=True,
        ) as mock_correct,
    ):
        response = client.put(
            "/reviews/1/correct",
            json=correction_data,
        )

    assert response.status_code == 200
    assert response.json() == corrected_record.model_dump()

    mock_correct.assert_called_once()
    received_id, received_correction = mock_correct.call_args.args
    assert received_id == 1
    assert received_correction == correction