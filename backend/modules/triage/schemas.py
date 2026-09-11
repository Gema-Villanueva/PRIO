from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# Definimos los datos necesarios para solicitar un triaje.
class TriageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    user_role: Literal["guest", "host"]

    # Eliminamos espacios exteriores y rechazamos mensajes sin contenido.
    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        cleaned_message = value.strip()

        if not cleaned_message:
            raise ValueError("Message must contain non-whitespace characters")

        return cleaned_message


# Definimos la estructura del resultado del triaje.
class TriageResponse(BaseModel):
    category: Literal[
        "access",
        "booking",
        "payment",
        "accommodation",
        "guest_behavior",
        "safety",
        "general",
    ]
    urgency: Literal["low", "medium", "high", "critical"]

    # Indicamos quién debe atender inicialmente la solicitud.
    responsible_party: Literal["host", "platform"]

    summary: str = Field(min_length=1)
    # El departamento solo aplica cuando la solicitud va a la plataforma.
    department: Literal[
        "reservation_support",
        "payments",
        "property_support",
        "trust_and_safety",
        "general_support",
    ] | None

    # Exigimos un resumen breve y normalizamos los espacios.
    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        words = value.split()

        if not 5 <= len(words) <= 25:
            raise ValueError(
                f"Summary must contain between 5 and 25 words; "
                f"received {len(words)}. "
                "Rewrite it in natural Spanish without adding unsupported details."
            )

        return " ".join(words)

    # Comprobamos que el departamento corresponde al destinatario.
    @model_validator(mode="after")
    def validate_department_assignment(self):
        platform_only_categories = {
            "booking",
            "payment",
            "guest_behavior",
            "safety",
        }
        expected_departments = {
            "access": "reservation_support",
            "booking": "reservation_support",
            "payment": "payments",
            "accommodation": "property_support",
            "guest_behavior": "trust_and_safety",
            "safety": "trust_and_safety",
            "general": "general_support",
        }

        if (
            self.category in platform_only_categories
            and self.responsible_party != "platform"
        ):
            raise ValueError(
                f"Category {self.category} must be handled by platform."
            )

        if self.category == "safety" and self.urgency != "critical":
            raise ValueError("Category safety must have critical urgency.")

        if self.responsible_party == "host" and self.department is not None:
            raise ValueError(
                "Department must be null when responsible_party is host."
            )

        if self.responsible_party == "platform" and self.department is None:
            raise ValueError(
                "Department is required when responsible_party is platform."
            )

        if (
            self.responsible_party == "platform"
            and self.department != expected_departments[self.category]
        ):
            raise ValueError(
                f"Category {self.category} must use department "
                f"{expected_departments[self.category]} when handled by platform."
            )

        return self


# Recogemos el consumo total de todas las llamadas necesarias para el triaje.
class TriageMetrics(BaseModel):
    provider: str
    model: str
    attempts: int = Field(ge=1)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    latency_ms: float = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)


# La API devuelve la clasificación validada junto con sus métricas.
class TriageResult(TriageResponse):
    metrics: TriageMetrics


# Añadimos los datos que existen después de guardar el triaje.
class StoredTriageResult(TriageResult):
    request_id: int = Field(ge=1)
    review_status: Literal["pending"] = "pending"