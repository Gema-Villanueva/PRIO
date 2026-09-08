from typing import Literal

from pydantic import BaseModel, Field, field_validator


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
    summary: str = Field(min_length=1)
    department: Literal[
        "reservation_support",
        "payments",
        "property_support",
        "trust_and_safety",
        "general_support",
    ]

    # Normalizamos los espacios y exigimos un resumen de diez palabras.
    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        words = value.split()

        if len(words) != 10:
            raise ValueError("Summary must contain exactly 10 words")

        return " ".join(words)