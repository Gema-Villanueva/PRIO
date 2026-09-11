from backend.db.database import (
    approve_triage_request,
    correct_triage_request,
    get_triage_request,
    list_pending_requests,
    save_triage_request,
)
from backend.modules.triage.schemas import (
    TriageMetrics,
    TriageRequest,
    TriageResult,
)
from backend.modules.review.schemas import ReviewCorrection


# Comprobamos que una solicitud se guarda y puede recuperarse por su ID.
def test_save_and_get_triage_request(tmp_path):
    database_path = tmp_path / "test_prio.db"

    request = TriageRequest(
        message="Necesito cancelar una reserva.",
        user_role="guest",
    )

    result = TriageResult(
        category="booking",
        urgency="medium",
        responsible_party="platform",
        summary="El huésped solicita cancelar una reserva futura.",
        department="reservation_support",
        metrics=TriageMetrics(
            provider="ollama",
            model="llama3.2:3b",
            attempts=1,
            input_tokens=80,
            output_tokens=15,
            latency_ms=1200.0,
            estimated_cost_usd=0.0,
        ),
    )

    request_id = save_triage_request(
        request,
        result,
        database_path,
    )

    saved_request = get_triage_request(
        request_id,
        database_path,
    )

    assert saved_request is not None
    assert saved_request["id"] == request_id
    assert saved_request["message"] == request.message
    assert saved_request["llm_category"] == result.category
    assert saved_request["llm_summary"] == result.summary
    assert saved_request["provider"] == "ollama"
    assert saved_request["input_tokens"] == 80
    assert saved_request["review_status"] == "pending"
    assert saved_request["final_category"] is None

    # Guardamos una segunda solicitud para comprobar el orden de la cola.
    second_request_id = save_triage_request(
        request,
        result,
        database_path,
    )

    pending_requests = list_pending_requests(database_path)

    assert len(pending_requests) == 2
    assert pending_requests[0]["id"] == request_id
    assert pending_requests[1]["id"] == second_request_id

    # Aprobamos la primera propuesta del LLM.
    was_approved = approve_triage_request(
        request_id,
        database_path,
    )

    approved_request = get_triage_request(
        request_id,
        database_path,
    )

    assert was_approved is True
    assert approved_request["review_status"] == "approved"
    assert approved_request["final_category"] == result.category
    assert approved_request["final_urgency"] == result.urgency
    assert approved_request["final_summary"] == result.summary
    assert approved_request["reviewed_at"] is not None

    # La solicitud aprobada ya no debe aparecer entre las pendientes.
    remaining_requests = list_pending_requests(database_path)

    assert len(remaining_requests) == 1
    assert remaining_requests[0]["id"] == second_request_id

    # Una solicitud ya revisada no puede aprobarse otra vez.
    assert approve_triage_request(request_id, database_path) is False

    # Corregimos la segunda propuesta y aumentamos su prioridad.
    correction = ReviewCorrection(
        category="booking",
        urgency="high",
        responsible_party="platform",
        summary="El huésped necesita cancelar una reserva con atención prioritaria.",
        department="reservation_support",
        review_notes="La llegada está próxima.",
    )

    was_corrected = correct_triage_request(
        second_request_id,
        correction,
        database_path,
    )

    corrected_request = get_triage_request(
        second_request_id,
        database_path,
    )

    assert was_corrected is True
    assert corrected_request["review_status"] == "corrected"

    # Conservamos la propuesta original y guardamos aparte la decisión humana.
    assert corrected_request["llm_urgency"] == "medium"
    assert corrected_request["final_urgency"] == "high"
    assert corrected_request["final_summary"] == correction.summary
    assert corrected_request["review_notes"] == "La llegada está próxima."
    assert corrected_request["reviewed_at"] is not None

    # Ya no debe quedar ninguna solicitud pendiente.
    assert list_pending_requests(database_path) == []

    # Una solicitud corregida no puede volver a corregirse.
    assert (
        correct_triage_request(
            second_request_id,
            correction,
            database_path,
        )
        is False
    )

    # Un identificador inexistente debe devolver None.
    assert get_triage_request(999, database_path) is None