import json
import argparse
from pathlib import Path

import httpx
from pydantic import ValidationError

from backend.modules.triage.schemas import TriageRequest
from backend.modules.triage.services import classify_request


# Localizamos los casos desde la carpeta principal del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = PROJECT_ROOT / "data" / "demo_cases.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PRIO triage classifications")
    parser.add_argument(
        "--cases",
        type=Path,
        default=CASES_PATH,
        help="Path to the JSON file containing the evaluation cases",
    )
    arguments = parser.parse_args()

    cases_path = arguments.cases
    if not cases_path.is_absolute():
        cases_path = PROJECT_ROOT / cases_path

    cases = json.loads(cases_path.read_text(encoding="utf-8"))

    valid_results = 0
    matching_results = 0
    total_attempts = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_latency_ms = 0.0
    total_cost_usd = 0.0

    for case in cases:
        print(f"\n--- {case['id']} ---")

        # Enviamos solo el mensaje y el rol, nunca la respuesta esperada.
        request = TriageRequest(
            message=case["message"],
            user_role=case["user_role"],
        )

        try:
            result = classify_request(request)
        except (ValidationError, httpx.HTTPError) as error:
            # Un fallo en un caso no impide evaluar los siguientes.
            print(f"ERROR: {error}")
            continue

        valid_results += 1
        result_data = result.model_dump()
        total_attempts += result.metrics.attempts
        total_input_tokens += result.metrics.input_tokens
        total_output_tokens += result.metrics.output_tokens
        total_latency_ms += result.metrics.latency_ms
        total_cost_usd += result.metrics.estimated_cost_usd

        # Comparamos los cuatro campos de clasificación.
        differences = {
            field: {
                "expected": expected_value,
                "actual": result_data[field],
            }
            for field, expected_value in case["expected"].items()
            if result_data[field] != expected_value
        }

        if differences:
            print("Classification: FAIL")
            print(json.dumps(differences, ensure_ascii=False, indent=2))
        else:
            matching_results += 1
            print("Classification: PASS")

        # Mostramos ambos resúmenes para revisar su significado a mano.
        print(f"Model summary: {result.summary}")
        print(f"Reference summary: {case['summary_reference']}")
        print(
            f"Metrics: {result.metrics.attempts} attempt(s), "
            f"{result.metrics.input_tokens} input tokens, "
            f"{result.metrics.output_tokens} output tokens, "
            f"{result.metrics.latency_ms:.2f} ms, "
            f"${result.metrics.estimated_cost_usd:.8f}"
        )

    print(f"\nValid responses: {valid_results}/{len(cases)}")
    print(f"Matching classifications: {matching_results}/{len(cases)}")
    print(f"Total attempts: {total_attempts}")
    print(f"Total input tokens: {total_input_tokens}")
    print(f"Total output tokens: {total_output_tokens}")
    print(f"Total latency: {total_latency_ms:.2f} ms")
    print(f"Estimated API cost: ${total_cost_usd:.8f}")


# Ejecutamos la evaluación solo cuando arrancamos este archivo.
if __name__ == "__main__":
    main()
