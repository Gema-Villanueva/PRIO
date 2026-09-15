import streamlit as st

from frontend.api_client import check_api_health
from frontend.styles import (
    apply_global_styles,
    render_admin_navigation,
)


# Esta aplicación está destinada al equipo interno.
st.set_page_config(
    page_title="Panel interno | PRIO",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()
render_admin_navigation()


# Cabecera principal del panel de operaciones.
st.markdown(
    """
    <div class="prio-hero">
        <h1>PRIO</h1>
        <p>Panel interno de clasificación y revisión</p>
        <p>
            Supervisa las solicitudes recibidas, valida las decisiones
            de la inteligencia artificial y compara los modelos.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# Avisamos al equipo si el backend está disponible.
if check_api_health():
    st.success("API conectada y preparada para procesar solicitudes.")
else:
    st.warning(
        "La API no está disponible. Inicia FastAPI para utilizar "
        "las funciones de PRIO."
    )


st.subheader("Herramientas internas")


# Primera fila: revisión, bandejas e histórico.
review_column, inbox_column, history_column = st.columns(3)


with review_column:
    st.markdown(
        """
        <div class="prio-card">
            <h3>Revisión de solicitudes pendientes</h3>
            <p class="prio-muted">
                Consulta las solicitudes pendientes y aprueba o corrige
                la clasificación propuesta por el modelo.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.page_link(
        "pages/1_Review.py",
        label="Revisar solicitudes",
        icon="✅",
        use_container_width=True,
    )


with inbox_column:
    st.markdown(
        """
        <div class="prio-card">
            <h3>Bandejas</h3>
            <p class="prio-muted">
                Consulta las solicitudes derivadas al anfitrión
                o a los departamentos y actualiza su estado.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.page_link(
        "pages/5_Inboxes.py",
        label="Gestionar bandejas",
        icon="📥",
        use_container_width=True,
    )


with history_column:
    st.markdown(
        """
        <div class="prio-card">
            <h3>Historial</h3>
            <p class="prio-muted">
                Consulta las solicitudes revisadas y sigue su destino
                y estado de gestión.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.page_link(
        "pages/2_History.py",
        label="Consultar historial",
        icon="🗂️",
        use_container_width=True,
    )


# Segunda fila: comparación y configuración.
metrics_column, settings_column = st.columns(2)


with metrics_column:
    st.markdown(
        """
        <div class="prio-card">
            <h3>Comparar modelos</h3>
            <p class="prio-muted">
                Compara Ollama y Groq mediante calidad, latencia,
                tokens consumidos y coste estimado.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.page_link(
        "pages/3_Metrics.py",
        label="Ver métricas",
        icon="📊",
        use_container_width=True,
    )

with settings_column:
    st.markdown(
        """
        <div class="prio-card">
            <h3>Configuración</h3>
            <p class="prio-muted">
                Selecciona el proveedor utilizado por PRIO
                o activa el modo automático con respaldo local.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.page_link(
        "pages/4_Settings.py",
        label="Configurar proveedor",
        icon="⚙️",
        use_container_width=True,
    )

st.divider()

st.caption(
    "Las clasificaciones generadas por PRIO son propuestas y requieren "
    "validación humana antes de su registro definitivo."
)
