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
            justification="La cancelación requiere una gestión sin peligro inmediato.",
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
        patch(
            "backend.modules.review.routes.dispatch_reviewed_request",
            return_value=1,
        ) as mock_dispatch,
    ):
        response = client.post("/reviews/1/approve")

    assert response.status_code == 200
    assert response.json() == approved_record.model_dump()
    mock_approve.assert_called_once_with(1)
    mock_dispatch.assert_called_once_with(approved_record)


# Comprobamos que una persona puede corregir la propuesta.
def test_correct_review():
    pending_record = create_pending_record()

    correction_data = {
        "category": "booking",
        "urgency": "high",
        "responsible_party": "platform",
        "summary": "El huésped necesita cancelar una reserva con atención prioritaria.",
        "justification": "La llegada próxima requiere gestionar la cancelación con mayor prioridad.",
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
        patch(
            "backend.modules.review.routes.dispatch_reviewed_request",
            return_value=1,
        ) as mock_dispatch,
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
    mock_dispatch.assert_called_once_with(corrected_record)

# Comprobamos que la API devuelve el histórico de solicitudes revisadas.
def test_get_completed_reviews():
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

    with patch(
        "backend.modules.review.routes.list_completed_review_records",
        return_value=[approved_record],
    ):
        response = client.get("/reviews/completed")

    assert response.status_code == 200
    assert response.json() == [approved_record.model_dump()]


# Comprobamos que la API devuelve las solicitudes derivadas.
def test_get_dispatches():
    dispatch = {
        "id": 1,
        "request_id": 8,
        "dispatch_type": "department_assignment",
        "destination": "Pagos y facturación",
        "message": "Nueva solicitud asignada a Pagos y facturación.",
        "status": "new",
        "created_at": "2026-09-15 10:00:00",
    }

    with patch(
        "backend.modules.review.routes.list_dispatches",
        return_value=[dispatch],
    ):
        response = client.get("/reviews/dispatches")

    assert response.status_code == 200
    assert response.json() == [dispatch]


# Comprobamos que puede cambiarse el estado de una derivación.
def test_change_dispatch_status():
    updated_dispatch = {
        "id": 1,
        "request_id": 8,
        "dispatch_type": "department_assignment",
        "destination": "Pagos y facturación",
        "message": "Nueva solicitud asignada a Pagos y facturación.",
        "status": "in_progress",
        "created_at": "2026-09-15 10:00:00",
    }

    with (
        patch(
            "backend.modules.review.routes.update_dispatch_status",
            return_value=True,
        ) as mock_update,
        patch(
            "backend.modules.review.routes.list_dispatches",
            return_value=[updated_dispatch],
        ),
    ):
        response = client.put(
            "/reviews/dispatches/1/status",
            json={"status": "in_progress"},
        )

    assert response.status_code == 200
    assert response.json() == updated_dispatch
    mock_update.assert_called_once_with(
        dispatch_id=1,
        status="in_progress",
    )


# Comprobamos la respuesta al actualizar una derivación inexistente.
def test_change_dispatch_status_returns_404():
    with patch(
        "backend.modules.review.routes.update_dispatch_status",
        return_value=False,
    ):
        response = client.put(
            "/reviews/dispatches/999/status",
            json={"status": "resolved"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Dispatch not found."}
