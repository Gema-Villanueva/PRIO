from typing import Literal


# Modos disponibles para procesar las solicitudes.
ProviderMode = Literal["auto", "groq", "ollama"]


# La configuración se mantiene mientras FastAPI está funcionando.
# Al reiniciar el servidor vuelve al modo automático.
_current_provider_mode: ProviderMode = "auto"


def get_provider_mode() -> ProviderMode:
    """Devuelve el modo seleccionado por el equipo."""

    return _current_provider_mode


def set_provider_mode(provider_mode: ProviderMode) -> ProviderMode:
    """Cambia el modo utilizado para las nuevas solicitudes."""

    global _current_provider_mode

    _current_provider_mode = provider_mode

    return _current_provider_mode