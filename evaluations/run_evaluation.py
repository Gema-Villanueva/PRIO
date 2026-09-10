import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from backend.modules.triage.schemas import TriageRequest
from backend.modules.triage.services import classify_request


# Localizamos los casos desde la carpeta principal del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = PROJECT_ROOT / "data" / "demo_cases.json"


def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    valid_results = 0
    matching_results = 0

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

    print(f"\nValid responses: {valid_results}/{len(cases)}")
    print(f"Matching classifications: {matching_results}/{len(cases)}")


# Ejecutamos la evaluación solo cuando arrancamos este archivo.
if __name__ == "__main__":
    main()