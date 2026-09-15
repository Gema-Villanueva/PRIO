import streamlit as st

from frontend.styles import apply_global_styles


# Configuramos la página de comparación.
st.set_page_config(
    page_title="Comparación de modelos | PRIO",
    page_icon="📊",
    layout="wide",
)

apply_global_styles()


st.title("Comparación de modelos")

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