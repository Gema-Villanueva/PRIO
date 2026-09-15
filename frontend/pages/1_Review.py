import httpx
import streamlit as st

from frontend.api_client import (
    approve_review,
    correct_review,
    get_pending_reviews,
)
from frontend.styles import apply_global_styles


# Configuramos la página interna de revisión.
st.set_page_config(
    page_title="Revisión humana | PRIO",
    page_icon="✅",
    layout="wide",
)

apply_global_styles()


# Traducimos los valores técnicos del backend al español.
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
    None: "No aplica: lo atiende el anfitrión",
}

ROLE_LABELS = {
    "guest": "Huésped",
    "host": "Anfitrión",
}


st.title("Revisión humana")

st.write(
    "Panel interno para revisar las clasificaciones propuestas "
    "por la inteligencia artificial."
)


# Recuperamos desde FastAPI las solicitudes pendientes.
try:
    pending_reviews = get_pending_reviews()

except httpx.HTTPError:
    st.error(
        "No se pudieron cargar las solicitudes. "
        "Comprueba que FastAPI continúa funcionando."
    )
    st.stop()


# Si no existen solicitudes pendientes, mostramos una confirmación.
if not pending_reviews:
    st.success("No hay solicitudes pendientes de revisión.")

else:
    st.metric(
        "Solicitudes pendientes",
        len(pending_reviews),
    )

    # Creamos una sección desplegable para cada solicitud.
    for review in pending_reviews:
        proposal = review["proposal"]
        metrics = review["metrics"]
        request_id = review["request_id"]

        title = (
            f'Solicitud #{request_id} · '
            f'{URGENCY_LABELS[proposal["urgency"]]} · '
            f'{CATEGORY_LABELS[proposal["category"]]}'
        )

        with st.expander(title, expanded=False):
            st.caption(
                f'Enviada por: {ROLE_LABELS[review["user_role"]]} '
                f'· Fecha: {review["created_at"]}'
            )

            st.markdown("#### Mensaje original")
            st.write(review["message"])

            st.divider()

            # Presentamos los tres datos principales en columnas.
            category_column, urgency_column, responsible_column = (
                st.columns(3)
            )

            category_column.metric(
                "Categoría",
                CATEGORY_LABELS[proposal["category"]],
            )

            urgency_column.metric(
                "Prioridad",
                URGENCY_LABELS[proposal["urgency"]],
            )

            responsible_column.metric(
                "Responsable",
                RESPONSIBLE_LABELS[proposal["responsible_party"]],
            )

            st.markdown("#### Resumen")
            st.write(proposal["summary"])

            st.markdown("#### Justificación")
            st.write(proposal["justification"])

            st.markdown("#### Departamento")
            st.write(
                DEPARTMENT_LABELS[proposal["department"]]
            )

            st.markdown("#### Métricas técnicas")

            provider_column, latency_column, tokens_column = (
                st.columns(3)
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
                metrics["input_tokens"]
                + metrics["output_tokens"],
            )

            # Este botón confirma la propuesta de la inteligencia artificial.
            if st.button(
                "Aprobar clasificación",
                key=f"approve_{request_id}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    approve_review(request_id)

                    st.success(
                        "Clasificación aprobada correctamente."
                    )

                    # Recargamos la página para retirar la solicitud
                    # de la lista de pendientes.
                    st.rerun()

                except httpx.HTTPError:
                    st.error(
                        "No se pudo aprobar la solicitud."
                    )


                        # Si la propuesta no es correcta, el operador puede modificarla.
            with st.expander("Corregir clasificación"):
                with st.form(f"correction_form_{request_id}"):
                    corrected_category = st.selectbox(
                        "Categoría",
                        options=list(CATEGORY_LABELS),
                        index=list(CATEGORY_LABELS).index(
                            proposal["category"]
                        ),
                        format_func=lambda value: CATEGORY_LABELS[value],
                    )

                    corrected_urgency = st.selectbox(
                        "Prioridad",
                        options=list(URGENCY_LABELS),
                        index=list(URGENCY_LABELS).index(
                            proposal["urgency"]
                        ),
                        format_func=lambda value: URGENCY_LABELS[value],
                    )

                    corrected_responsible = st.selectbox(
                        "Responsable",
                        options=list(RESPONSIBLE_LABELS),
                        index=list(RESPONSIBLE_LABELS).index(
                            proposal["responsible_party"]
                        ),
                        format_func=lambda value: RESPONSIBLE_LABELS[value],
                    )

                    corrected_summary = st.text_area(
                        "Resumen",
                        value=proposal["summary"],
                        help="Debe contener entre 5 y 25 palabras.",
                    )

                    corrected_justification = st.text_area(
                        "Justificación",
                        value=proposal["justification"],
                        max_chars=500,
                    )

                    review_notes = st.text_area(
                        "Notas de la revisión",
                        placeholder=(
                            "Explica brevemente por qué has corregido "
                            "la propuesta."
                        ),
                        max_chars=1000,
                    )

                    correction_submitted = st.form_submit_button(
                        "Guardar corrección",
                        use_container_width=True,
                    )


                if correction_submitted:
                    # Algunas categorías solo pueden ser gestionadas
                    # por la plataforma.
                    platform_only_categories = {
                        "booking",
                        "payment",
                        "guest_behavior",
                        "safety",
                    }

                    expected_departments = {
                        "access": "reservation_support",
                        "booking": "reservation_support",
                        "payment": "payments",
                        "accommodation": "property_support",
                        "guest_behavior": "trust_and_safety",
                        "safety": "trust_and_safety",
                        "general": "general_support",
                    }

                    if corrected_category in platform_only_categories:
                        corrected_responsible = "platform"

                    # Los incidentes de seguridad siempre son críticos.
                    if corrected_category == "safety":
                        corrected_urgency = "critical"

                    # El departamento se calcula automáticamente para
                    # evitar asignaciones incompatibles.
                    if corrected_responsible == "platform":
                        corrected_department = expected_departments[
                            corrected_category
                        ]
                    else:
                        corrected_department = None

                    correction = {
                        "category": corrected_category,
                        "urgency": corrected_urgency,
                        "responsible_party": corrected_responsible,
                        "summary": corrected_summary,
                        "justification": corrected_justification,
                        "department": corrected_department,
                        "review_notes": review_notes or None,
                    }

                    try:
                        correct_review(
                            request_id=request_id,
                            correction=correction,
                        )

                        st.success(
                            "La corrección se ha guardado correctamente."
                        )

                        # Retiramos la solicitud de la cola de pendientes.
                        st.rerun()

                    except httpx.HTTPStatusError as error:
                        try:
                            detail = error.response.json().get(
                                "detail",
                                "La corrección no es válida.",
                            )
                        except ValueError:
                            detail = "La corrección no es válida."

                        st.error(
                            f"No se pudo guardar la corrección: {detail}"
                        )

                    except httpx.HTTPError:
                        st.error(
                            "No se pudo conectar con FastAPI."
                        )