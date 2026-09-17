import httpx
import streamlit as st

from frontend.api_client import compare_triage_providers
from frontend.styles import (
    apply_global_styles,
    render_admin_navigation,
)

# Configuramos la página de comparación.
st.set_page_config(
    page_title="Comparación de modelos | PRIO",
    page_icon="📊",
    layout="wide",
)

apply_global_styles()
render_admin_navigation()

st.title("Comparación de modelos")

st.write(
    "Compara Groq y Ollama con una solicitud en directo o consulta "
    "los resultados de la evaluación controlada."
)


CATEGORY_LABELS = {
    "access": "Acceso",
    "booking": "Reservas",
    "payment": "Pagos",
    "accommodation": "Alojamiento",
    "guest_behavior": "Comportamiento de huéspedes",
    "safety": "Seguridad",
    "general": "Información general",
}

URGENCY_LABELS = {
    "low": "Baja",
    "medium": "Media",
    "high": "Alta",
    "critical": "Crítica",
}

RESPONSIBLE_LABELS = {
    "host": "Anfitrión",
    "platform": "Plataforma",
}


st.subheader("Comparación en directo")

st.caption(
    "La misma solicitud se procesa una vez con Groq y otra con Ollama. "
    "Esta prueba no se guarda en Revisión ni en el Historial."
)

with st.form("live_comparison_form"):
    role_column, message_column = st.columns([1, 3])

    with role_column:
        comparison_role = st.selectbox(
            "¿Quién envía la solicitud?",
            options=["guest", "host"],
            format_func=lambda value: {
                "guest": "Huésped",
                "host": "Anfitrión",
            }[value],
        )

    with message_column:
        comparison_message = st.text_area(
            "Solicitud para comparar",
            placeholder=(
                "Ejemplo: He pagado la reserva, pero todavía "
                "aparece como pendiente."
            ),
            height=100,
        )

    compare_button = st.form_submit_button(
        "Comparar con Groq y Ollama",
        type="primary",
        use_container_width=True,
    )


if compare_button:
    if not comparison_message.strip():
        st.warning("Escribe una solicitud antes de iniciar la comparación.")

    else:
        try:
            with st.spinner(
                "Consultando Groq y Ollama. El modelo local puede tardar..."
            ):
                st.session_state["live_comparison"] = (
                    compare_triage_providers(
                        message=comparison_message,
                        user_role=comparison_role,
                    )
                )

        except httpx.HTTPError:
            st.error(
                "No se pudo completar la comparación. Comprueba que "
                "FastAPI, Groq y Ollama estén disponibles."
            )


def render_live_result(provider_name: str, result: dict) -> None:
    metrics = result["metrics"]
    destination = RESPONSIBLE_LABELS[result["responsible_party"]]

    st.markdown(f"### {provider_name}")
    st.write(f"**Categoría:** {CATEGORY_LABELS[result['category']]}")
    st.write(f"**Prioridad:** {URGENCY_LABELS[result['urgency']]}")
    st.write(f"**Responsable:** {destination}")
    st.write(f"**Resumen:** {result['summary']}")

    latency_column, tokens_column = st.columns(2)

    with latency_column:
        st.metric(
            "Latencia",
            f"{metrics['latency_ms'] / 1000:.2f} s",
        )

    with tokens_column:
        st.metric(
            "Tokens",
            metrics["input_tokens"] + metrics["output_tokens"],
        )

    st.caption(f"Coste estimado: ${metrics['estimated_cost_usd']:.8f}")


if "live_comparison" in st.session_state:
    live_results = st.session_state["live_comparison"]
    live_groq_column, live_ollama_column = st.columns(2)

    with live_groq_column:
        render_live_result("Groq", live_results["groq"])

    with live_ollama_column:
        render_live_result("Ollama", live_results["ollama"])


st.divider()
st.subheader("Evaluación de referencia")

st.write(
    "Resultados obtenidos al evaluar Ollama y Groq con los mismos "
    "10 casos de prueba de PRIO."
)


# Estos son los resultados de las evaluaciones que ya ejecutamos.
# Más adelante podremos guardarlos automáticamente en un archivo.
EVALUATION_RESULTS = {
    "ollama": {
        "name": "Ollama",
        "description": "Modelo local y privado",
        "valid_responses": 10,
        "matching_classifications": 10,
        "total_cases": 10,
        "attempts": 13,
        "input_tokens": 17579,
        "output_tokens": 801,
        "latency_seconds": 164.27,
        "cost_usd": 0.0,
    },
    "groq": {
        "name": "Groq",
        "description": "Proveedor externo con capa gratuita",
        "valid_responses": 10,
        "matching_classifications": 10,
        "total_cases": 10,
        "attempts": 10,
        "input_tokens": 15700,
        "output_tokens": 954,
        "latency_seconds": 11.22,
        "cost_usd": 0.0,
    },
}


ollama = EVALUATION_RESULTS["ollama"]
groq = EVALUATION_RESULTS["groq"]


# Mostramos un resumen separado para cada proveedor.
ollama_column, groq_column = st.columns(2)


with ollama_column:
    st.subheader("Ollama")
    st.caption(ollama["description"])

    st.metric(
        "Calidad de clasificación",
        (
            f'{ollama["matching_classifications"]}'
            f'/{ollama["total_cases"]}'
        ),
    )

    st.metric(
        "Tiempo total",
        f'{ollama["latency_seconds"]:.2f} s',
    )

    st.metric(
        "Coste estimado",
        f'${ollama["cost_usd"]:.8f}',
    )


with groq_column:
    st.subheader("Groq")
    st.caption(groq["description"])

    st.metric(
        "Calidad de clasificación",
        (
            f'{groq["matching_classifications"]}'
            f'/{groq["total_cases"]}'
        ),
    )

    st.metric(
        "Tiempo total",
        f'{groq["latency_seconds"]:.2f} s',
    )

    st.metric(
        "Coste estimado",
        f'${groq["cost_usd"]:.8f}',
    )


st.divider()

st.subheader("Comparación general")


# Streamlit convierte esta lista en una tabla interactiva.
comparison_table = [
    {
        "Proveedor": "Ollama",
        "Respuestas válidas": "10/10",
        "Clasificaciones correctas": "10/10",
        "Intentos": ollama["attempts"],
        "Tokens totales": (
            ollama["input_tokens"] + ollama["output_tokens"]
        ),
        "Latencia total": f'{ollama["latency_seconds"]:.2f} s',
        "Coste": f'${ollama["cost_usd"]:.8f}',
    },
    {
        "Proveedor": "Groq",
        "Respuestas válidas": "10/10",
        "Clasificaciones correctas": "10/10",
        "Intentos": groq["attempts"],
        "Tokens totales": (
            groq["input_tokens"] + groq["output_tokens"]
        ),
        "Latencia total": f'{groq["latency_seconds"]:.2f} s',
        "Coste": f'${groq["cost_usd"]:.8f}',
    },
]

st.dataframe(
    comparison_table,
    use_container_width=True,
    hide_index=True,
)


st.subheader("Latencia total en segundos")

# Cuanto más baja sea la barra, más rápido respondió el proveedor.
st.bar_chart(
    [
        {
            "Proveedor": "Ollama",
            "Segundos": ollama["latency_seconds"],
        },
        {
            "Proveedor": "Groq",
            "Segundos": groq["latency_seconds"],
        },
    ],
    x="Proveedor",
    y="Segundos",
)


st.subheader("Conclusión")

st.info(
    "Los dos proveedores clasificaron correctamente los 10 casos. "
    "Groq fue mucho más rápido, mientras que Ollama mantiene los datos "
    "en el equipo local y no depende de un servicio externo."
)

st.caption(
    "Resultados correspondientes a una ejecución concreta. "
    "La latencia puede cambiar según el ordenador, la conexión "
    "y la disponibilidad del proveedor."
)
