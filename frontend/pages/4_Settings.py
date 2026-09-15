import httpx
import streamlit as st

from frontend.api_client import (
    get_provider_configuration,
    update_provider_configuration,
)
from frontend.styles import (
    apply_global_styles,
    render_admin_navigation,
)


# Configuramos la página interna de selección de proveedor.
st.set_page_config(
    page_title="Configuración | PRIO",
    page_icon="⚙️",
    layout="wide",
)

apply_global_styles()
render_admin_navigation()

PROVIDER_LABELS = {
    "auto": "Automático",
    "groq": "Groq",
    "ollama": "Ollama",
}

PROVIDER_DESCRIPTIONS = {
    "auto": (
        "Utiliza Groq como primera opción y cambia a Ollama "
        "si el proveedor externo falla."
    ),
    "groq": (
        "Utiliza únicamente Groq. Ofrece menor latencia, "
        "pero depende de conexión y límites externos."
    ),
    "ollama": (
        "Utiliza únicamente Ollama. Procesa los datos localmente, "
        "pero puede tardar más."
    ),
}


st.title("Configuración del proveedor")

st.write(
    "Selecciona cómo procesará PRIO las próximas solicitudes. "
    "Esta opción es interna y no aparece en el portal del cliente."
)


# Consultamos la configuración actual de FastAPI.
try:
    configuration = get_provider_configuration()
    current_mode = configuration["mode"]

except httpx.HTTPError:
    st.error(
        "No se pudo consultar la configuración. "
        "Comprueba que FastAPI continúa funcionando."
    )
    st.stop()


# Sincronizamos el selector con el valor real guardado en FastAPI.
if st.session_state.get("provider_mode") != current_mode:
    st.session_state["provider_mode"] = current_mode


def save_provider_mode() -> None:
    """Guarda el modo justo después de que la persona lo seleccione."""

    selected_mode = st.session_state["provider_mode"]

    try:
        updated_configuration = update_provider_configuration(
            selected_mode
        )

        st.session_state["provider_message"] = (
            "Configuración guardada. Las próximas solicitudes "
            f'utilizarán el modo '
            f'**{PROVIDER_LABELS[updated_configuration["mode"]]}**.'
        )

    except httpx.HTTPError:
        st.session_state["provider_error"] = (
            "No se pudo guardar la configuración."
        )


st.info(
    f'Modo actual: **{PROVIDER_LABELS[current_mode]}**. '
    f'{PROVIDER_DESCRIPTIONS[current_mode]}'
)


st.radio(
    "Modo de procesamiento",
    options=["auto", "groq", "ollama"],
    format_func=lambda value: PROVIDER_LABELS[value],
    key="provider_mode",
    on_change=save_provider_mode,
)

selected_mode = st.session_state["provider_mode"]

st.caption(PROVIDER_DESCRIPTIONS[selected_mode])


if "provider_message" in st.session_state:
    st.success(
        st.session_state.pop("provider_message")
    )

if "provider_error" in st.session_state:
    st.error(
        st.session_state.pop("provider_error")
    )


st.divider()

st.caption(
    "La configuración vuelve al modo automático cuando "
    "se reinicia FastAPI."
)
