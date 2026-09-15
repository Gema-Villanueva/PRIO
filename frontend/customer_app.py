import httpx
import streamlit as st

from frontend.api_client import submit_triage
from frontend.styles import apply_global_styles


# Configuramos la pestaña del portal del cliente.
st.set_page_config(
    page_title="Enviar aviso | PRIO",
    page_icon="📱",
    layout="centered",
)

apply_global_styles()


# El cliente solo debe ver el formulario de envío.
# Ocultamos el menú interno y el botón que permite desplegarlo.
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }

        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Cabecera visible del portal de ayuda.
st.markdown(
    """
    <div class="prio-hero">
        <h1>PRIO Ayuda</h1>
        <p>Atención para huéspedes y anfitriones</p>
        <p>
            Envíanos tu aviso de forma sencilla y lo dirigiremos
            a la persona adecuada.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


st.subheader("¿Cómo podemos ayudarte?")

st.write(
    "Describe lo ocurrido con el mayor detalle posible. "
    "Analizaremos tu petición y nos pondremos en contacto contigo."
)

st.caption(
    "🔒 La información se utiliza únicamente para gestionar tu solicitud."
)


# Este formulario simula el apartado de ayuda de una aplicación móvil.
with st.form("customer_request_form", clear_on_submit=True):
    user_role = st.selectbox(
    "¿Quién eres?",
    options=[None, "guest", "host"],
    index=0,
    format_func=lambda value: {
        None: "Selecciona una opción",
        "guest": "Huésped",
        "host": "Anfitrión",
    }[value],
    )

    message = st.text_area(
        "Describe el problema",
        height=180,
        max_chars=5000,
        placeholder=(
            "Ejemplo: Estoy en la puerta del alojamiento y "
            "el código de acceso no funciona."
        ),
    )

    submitted = st.form_submit_button(
        "Enviar aviso",
        type="primary",
        use_container_width=True,
    )


if submitted:
    if user_role is None:
        st.warning("Selecciona si eres huésped o anfitrión.")

    elif not message.strip():
        st.warning("Escribe una descripción antes de enviar el aviso.")

    else:
        try:
            with st.spinner("Estamos enviando tu solicitud..."):
                # Solicitamos el modo automático configurado.
                # El cliente no necesita conocer ni elegir el proveedor utilizado.
                result = submit_triage(
                    message=message,
                    user_role=user_role,
                    provider="auto",
                )

            # Adaptamos la confirmación a la prioridad detectada,
            # pero no mostramos al cliente la clasificación interna.
            CUSTOMER_MESSAGES = {
                "low": (
                    "Hemos recibido correctamente su petición. "
                    "Nuestro equipo la revisará y se pondrá en contacto con usted."
                ),
                "medium": (
                    "Hemos recibido correctamente su petición. "
                    "La revisaremos con prioridad y nos pondremos en contacto "
                    "con usted a la mayor brevedad posible."
                ),
                "high": (
                    "Hemos recibido correctamente su petición y nuestro equipo "
                    "ya ha sido avisado. Nos pondremos en contacto con usted "
                    "lo antes posible."
                ),
                "critical": (
                    "Hemos recibido correctamente su petición y la hemos marcado "
                    "para atención prioritaria. Nuestro equipo actuará lo antes posible. "
                    "Si existe un peligro inmediato, contacte con los servicios de emergencia."
                ),
            }

            customer_message = CUSTOMER_MESSAGES[result["urgency"]]

            st.success(customer_message)

        except httpx.HTTPStatusError as error:
            try:
                detail = error.response.json().get(
                    "detail",
                    "No hemos podido procesar la solicitud.",
                )
            except ValueError:
                detail = "No hemos podido procesar la solicitud."

            st.error(detail)

        except httpx.HTTPError:
            st.error(
                "No hemos podido conectar con el servicio. "
                "Inténtalo de nuevo dentro de unos minutos."
            )


st.divider()

st.caption(
    "Si existe un peligro inmediato para las personas, "
    "contacta con los servicios de emergencia."
)