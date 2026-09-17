import httpx
import streamlit as st

from frontend.api_client import (
    get_dispatches,
    update_dispatch_status,
)
from frontend.styles import (
    apply_global_styles,
    render_admin_navigation,
)


st.set_page_config(
    page_title="Bandejas | PRIO",
    page_icon="📥",
    layout="wide",
)

apply_global_styles()
render_admin_navigation()


STATUS_LABELS = {
    "new": "Nueva",
    "in_progress": "En gestión",
    "resolved": "Resuelta",
}

TYPE_LABELS = {
    "host_notification": "Notificación al anfitrión",
    "department_assignment": "Derivación a departamento",
}

SORT_OPTIONS = {
    "request_id": "Número de solicitud",
    "destination": "Destino",
    "status": "Estado",
    "created_at": "Fecha",
}

STATUS_ORDER = {
    "new": 0,
    "in_progress": 1,
    "resolved": 2,
}


st.title("Bandejas")

st.write(
    "Consulta las solicitudes derivadas al anfitrión "
    "o a los departamentos de la plataforma."
)


try:
    dispatches = get_dispatches()

except httpx.HTTPError:
    st.error(
        "No se pudieron cargar las bandejas. "
        "Comprueba que FastAPI continúa funcionando."
    )
    st.stop()


if not dispatches:
    st.info("Todavía no hay solicitudes derivadas.")
    st.stop()


status_options = ["all", "new", "in_progress", "resolved"]
destination_options = [
    "Anfitrión",
    "Soporte de reservas",
    "Pagos y facturación",
    "Soporte del alojamiento",
    "Confianza y seguridad",
    "Atención general",
]

status_column, destination_column = st.columns(2)

with status_column:
    selected_status = st.selectbox(
        "Estado",
        options=status_options,
        format_func=lambda value: {
            "all": "Todos",
            **STATUS_LABELS,
        }[value],
    )

with destination_column:
    selected_destination = st.selectbox(
        "Vista de bandeja",
        options=["all", *destination_options],
        format_func=lambda value: (
            "Vista general" if value == "all" else value
        ),
    )


sort_column, direction_column = st.columns(2)

with sort_column:
    selected_sort = st.selectbox(
        "Ordenar por",
        options=list(SORT_OPTIONS),
        format_func=lambda value: SORT_OPTIONS[value],
        index=3,
    )

with direction_column:
    selected_direction = st.selectbox(
        "Orden",
        options=["descending", "ascending"],
        format_func=lambda value: {
            "descending": "Descendente",
            "ascending": "Ascendente",
        }[value],
    )


filtered_dispatches = []

for dispatch in dispatches:
    if (
        selected_status != "all"
        and dispatch["status"] != selected_status
    ):
        continue

    if (
        selected_destination != "all"
        and dispatch["destination"] != selected_destination
    ):
        continue

    filtered_dispatches.append(dispatch)


def dispatch_sort_value(dispatch: dict):
    if selected_sort == "status":
        return STATUS_ORDER[dispatch["status"]]

    if selected_sort == "destination":
        return dispatch["destination"].casefold()

    return dispatch[selected_sort]


filtered_dispatches.sort(
    key=dispatch_sort_value,
    reverse=selected_direction == "descending",
)


if not filtered_dispatches:
    st.warning("No hay derivaciones que coincidan con los filtros.")
    st.stop()


table_rows = [
    {
        "Solicitud": f"#{dispatch['request_id']}",
        "Tipo": TYPE_LABELS[dispatch["dispatch_type"]],
        "Destino": dispatch["destination"],
        "Mensaje": dispatch["message"],
        "Estado": STATUS_LABELS[dispatch["status"]],
        "Fecha": dispatch["created_at"],
    }
    for dispatch in filtered_dispatches
]


st.subheader("Solicitudes derivadas")

st.dataframe(
    table_rows,
    use_container_width=True,
    hide_index=True,
)

st.divider()
st.subheader("Gestionar una solicitud")

selected_dispatch_id = st.selectbox(
    "Selecciona una solicitud derivada",
    options=[
        dispatch["id"]
        for dispatch in filtered_dispatches
    ],
    format_func=lambda dispatch_id: next(
        (
            f"Solicitud #{dispatch['request_id']} · "
            f"{dispatch['destination']}"
            for dispatch in filtered_dispatches
            if dispatch["id"] == dispatch_id
        ),
        str(dispatch_id),
    ),
)

selected_dispatch = next(
    dispatch
    for dispatch in filtered_dispatches
    if dispatch["id"] == selected_dispatch_id
)

st.write(selected_dispatch["message"])

current_status = selected_dispatch["status"]

st.write(
    f"**Estado actual:** {STATUS_LABELS[current_status]}"
)


try:
    if current_status == "new":
        if st.button(
            "Comenzar gestión",
            type="primary",
            use_container_width=True,
        ):
            update_dispatch_status(
                dispatch_id=selected_dispatch_id,
                status="in_progress",
            )
            st.success("La solicitud está ahora en gestión.")
            st.rerun()

    elif current_status == "in_progress":
        if st.button(
            "Marcar como resuelta",
            type="primary",
            use_container_width=True,
        ):
            update_dispatch_status(
                dispatch_id=selected_dispatch_id,
                status="resolved",
            )
            st.success("La solicitud se ha marcado como resuelta.")
            st.rerun()

    else:
        st.success("Esta solicitud ya está resuelta.")

except httpx.HTTPError:
    st.error(
        "No se pudo cambiar el estado. "
        "Comprueba que FastAPI continúa funcionando."
    )
