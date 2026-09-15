import streamlit as st

from frontend.api_client import check_api_health
from frontend.styles import apply_global_styles


# Esta aplicación está destinada al equipo interno.
st.set_page_config(
    page_title="Panel interno | PRIO",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()


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


st.subheader("Herramientas del equipo")


# El panel interno ofrece revisión, histórico y métricas.
review_column, history_column, metrics_column = st.columns(3)


with review_column:
    st.markdown(
        """
        <div class="prio-card">
            <h3>Revisión humana</h3>
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


with history_column:
    st.markdown(
        """
        <div class="prio-card">
            <h3>Historial</h3>
            <p class="prio-muted">
                Consulta las solicitudes aprobadas o corregidas
                y compara la propuesta con la decisión final.
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


st.divider()

st.caption(
    "Las clasificaciones generadas por PRIO son propuestas y requieren "
    "validación humana antes de su registro definitivo."
)