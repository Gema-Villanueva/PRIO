import httpx
import streamlit as st

from frontend.api_client import (
    get_completed_reviews,
    get_dispatches,
)
from frontend.styles import (
    apply_global_styles,
    render_admin_navigation,
)


# Configuramos la página del histórico.
st.set_page_config(
    page_title="Historial | PRIO",
    page_icon="🗂️",
    layout="wide",
)

apply_global_styles()
render_admin_navigation()

# Traducimos los valores internos para mostrarlos en español.
STATUS_LABELS = {
    "approved": "Aprobada",
    "corrected": "Corregida",
}

DISPATCH_STATUS_LABELS = {
    "new": "Nueva",
    "in_progress": "En gestión",
    "resolved": "Resuelta",
}

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

DEPARTMENT_LABELS = {
    "reservation_support": "Soporte de reservas",
    "payments": "Pagos",
    "property_support": "Soporte del alojamiento",
    "trust_and_safety": "Confianza y seguridad",
    "general_support": "Soporte general",
    None: "No aplica",
}

ROLE_LABELS = {
    "guest": "Huésped",
    "host": "Anfitrión",
}


st.title("Historial de solicitudes")

st.write(
    "Consulta las solicitudes que ya han sido aprobadas o corregidas "
    "por el equipo de revisión."
)


# Recuperamos el histórico desde FastAPI.
try:
    completed_reviews = get_completed_reviews()
    dispatches = get_dispatches()

except httpx.HTTPError:
    st.error(
        "No se pudo cargar el histórico. "
        "Comprueba que FastAPI continúa funcionando."
    )
    st.stop()


if not completed_reviews:
    st.info("Todavía no hay solicitudes revisadas.")
    st.stop()


# Relacionamos cada solicitud revisada con su derivación.
dispatch_by_request_id = {
    dispatch["request_id"]: dispatch
    for dispatch in dispatches
}


# Permitimos filtrar el histórico.
status_column, category_column, urgency_column, management_column = (
    st.columns(4)
)

with status_column:
    selected_status = st.selectbox(
        "Estado",
        options=["all", "approved", "corrected"],
        format_func=lambda value: {
            "all": "Todos",
            "approved": "Aprobadas",
            "corrected": "Corregidas",
        }[value],
    )

with category_column:
    selected_category = st.selectbox(
        "Categoría",
        options=["all", *CATEGORY_LABELS],
        format_func=lambda value: (
            "Todas"
            if value == "all"
            else CATEGORY_LABELS[value]
        ),
    )

with urgency_column:
    selected_urgency = st.selectbox(
        "Prioridad",
        options=["all", *URGENCY_LABELS],
        format_func=lambda value: (
            "Todas"
            if value == "all"
            else URGENCY_LABELS[value]
        ),
    )

with management_column:
    selected_management = st.selectbox(
        "Gestión",
        options=["all", "new", "in_progress", "resolved", "no_record"],
        format_func=lambda value: {
            "all": "Todas",
            **DISPATCH_STATUS_LABELS,
            "no_record": "Sin registro",
        }[value],
    )


# Aplicamos los filtros sobre la decisión humana final.
filtered_reviews = []

for review in completed_reviews:
    final_decision = review["final_decision"]
    dispatch = dispatch_by_request_id.get(review["request_id"])

    if final_decision is None:
        continue

    if (
        selected_status != "all"
        and review["review_status"] != selected_status
    ):
        continue

    if (
        selected_category != "all"
        and final_decision["category"] != selected_category
    ):
        continue

    if (
        selected_urgency != "all"
        and final_decision["urgency"] != selected_urgency
    ):
        continue

    management_status = dispatch["status"] if dispatch else "no_record"

    if (
        selected_management != "all"
        and management_status != selected_management
    ):
        continue

    filtered_reviews.append(review)


if not filtered_reviews:
    st.warning("No hay solicitudes que coincidan con los filtros.")
    st.stop()


st.subheader("Solicitudes revisadas")


# Creamos una versión resumida para la tabla.
history_table = []

for review in filtered_reviews:
    final_decision = review["final_decision"]
    dispatch = dispatch_by_request_id.get(review["request_id"])

    history_table.append(
        {
            "ID": review["request_id"],
            "Estado": STATUS_LABELS[review["review_status"]],
            "Categoría": CATEGORY_LABELS[
                final_decision["category"]
            ],
            "Prioridad": URGENCY_LABELS[
                final_decision["urgency"]
            ],
            "Responsable": RESPONSIBLE_LABELS[
                final_decision["responsible_party"]
            ],
            "Departamento": DEPARTMENT_LABELS[
                final_decision["department"]
            ],
            "Destino": (
                dispatch["destination"]
                if dispatch
                else "Sin registro"
            ),
            "Gestión": (
                DISPATCH_STATUS_LABELS[dispatch["status"]]
                if dispatch
                else "Sin registro"
            ),
            "Fecha de revisión": review["reviewed_at"],
        }
    )


st.dataframe(
    history_table,
    use_container_width=True,
    hide_index=True,
)


st.divider()

st.subheader("Detalle de una solicitud")


# Elegimos qué solicitud queremos inspeccionar.
selected_request_id = st.selectbox(
    "Selecciona una solicitud",
    options=[
        review["request_id"]
        for review in filtered_reviews
    ],
    format_func=lambda request_id: f"Solicitud #{request_id}",
)


selected_review = next(
    review
    for review in filtered_reviews
    if review["request_id"] == selected_request_id
)

proposal = selected_review["proposal"]
final_decision = selected_review["final_decision"]
metrics = selected_review["metrics"]
selected_dispatch = dispatch_by_request_id.get(selected_request_id)


st.markdown("#### Mensaje original")

st.write(selected_review["message"])

st.caption(
    f'Enviada por: {ROLE_LABELS[selected_review["user_role"]]} '
    f'· Creada: {selected_review["created_at"]} '
    f'· Revisada: {selected_review["reviewed_at"]}'
)


# Mostramos la propuesta y la decisión final una al lado de la otra.
proposal_column, final_column = st.columns(2)


with proposal_column:
    st.markdown("### Propuesta de la IA")

    st.write(
        f'**Categoría:** '
        f'{CATEGORY_LABELS[proposal["category"]]}'
    )

    st.write(
        f'**Prioridad:** '
        f'{URGENCY_LABELS[proposal["urgency"]]}'
    )

    st.write(
        f'**Responsable:** '
        f'{RESPONSIBLE_LABELS[proposal["responsible_party"]]}'
    )

    st.write(
        f'**Departamento:** '
        f'{DEPARTMENT_LABELS[proposal["department"]]}'
    )

    st.write(f'**Resumen:** {proposal["summary"]}')

    st.write(
        f'**Justificación:** {proposal["justification"]}'
    )


with final_column:
    st.markdown("### Decisión humana final")

    st.write(
        f'**Categoría:** '
        f'{CATEGORY_LABELS[final_decision["category"]]}'
    )

    st.write(
        f'**Prioridad:** '
        f'{URGENCY_LABELS[final_decision["urgency"]]}'
    )

    st.write(
        f'**Responsable:** '
        f'{RESPONSIBLE_LABELS[final_decision["responsible_party"]]}'
    )

    st.write(
        f'**Departamento:** '
        f'{DEPARTMENT_LABELS[final_decision["department"]]}'
    )

    st.write(
        f'**Resumen:** {final_decision["summary"]}'
    )

    st.write(
        f'**Justificación:** '
        f'{final_decision["justification"]}'
    )


# Indicamos si una persona cambió algún campo.
if selected_review["review_status"] == "approved":
    st.success(
        "La propuesta de la inteligencia artificial "
        "fue aprobada sin cambios."
    )

else:
    st.warning(
        "La propuesta fue corregida durante la revisión humana."
    )

    if final_decision["review_notes"]:
        st.write(
            f'**Notas de revisión:** '
            f'{final_decision["review_notes"]}'
        )


st.markdown("#### Derivación")

if selected_dispatch:
    destination_column, management_column = st.columns(2)

    destination_column.metric(
        "Destino",
        selected_dispatch["destination"],
    )
    management_column.metric(
        "Estado de gestión",
        DISPATCH_STATUS_LABELS[selected_dispatch["status"]],
    )

    st.write(selected_dispatch["message"])

else:
    st.info(
        "Esta solicitud fue revisada antes de incorporar "
        "las bandejas internas."
    )


st.markdown("#### Métricas de la petición")

provider_column, latency_column, tokens_column, cost_column = (
    st.columns(4)
)

provider_column.metric(
    "Proveedor",
    metrics["provider"].title(),
)

latency_column.metric(
    "Latencia",
    f'{metrics["latency_ms"] / 1000:.2f} s',
)

tokens_column.metric(
    "Tokens",
    metrics["input_tokens"] + metrics["output_tokens"],
)

cost_column.metric(
    "Coste estimado",
    f'${metrics["estimated_cost_usd"]:.8f}',
)
