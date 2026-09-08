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