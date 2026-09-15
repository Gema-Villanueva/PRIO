import streamlit as st


def apply_global_styles() -> None:
    """Aplica el estilo visual común a todas las páginas de PRIO."""

    # Streamlit permite incluir CSS dentro de la página mediante st.markdown.
    # unsafe_allow_html=True es necesario para que interprete las etiquetas
    # de estilo en lugar de mostrarlas como texto.
    st.markdown(
        """
        <style>
        /* Definimos los colores principales de PRIO. */
        :root {
            --prio-navy: #17324d;
            --prio-blue: #2f6fed;
            --prio-light-blue: #eaf1ff;
            --prio-background: #f5f7fb;
            --prio-text: #1f2937;
            --prio-muted: #64748b;
            --prio-border: #dbe3ef;
        }

        /* Aplicamos un fondo suave a toda la aplicación. */
        .stApp {
            background-color: var(--prio-background);
            color: var(--prio-text);
        }

        /* Limitamos el ancho para que el contenido resulte más legible. */
        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* Estilo del título principal. */
        h1 {
            color: var(--prio-navy);
            font-weight: 750;
            letter-spacing: -0.03em;
        }

        /* Estilo de los títulos de sección. */
        h2, h3 {
            color: var(--prio-navy);
        }

        /* Tarjeta reutilizable para destacar información. */
        .prio-card {
            background: white;
            border: 1px solid var(--prio-border);
            border-radius: 16px;
            padding: 1.25rem;
            box-shadow: 0 8px 24px rgba(23, 50, 77, 0.06);
            margin-bottom: 1rem;
        }

        /* Cabecera destacada de la página principal. */
        .prio-hero {
            padding: 2rem;
            border-radius: 20px;
            color: white;
            background:
                linear-gradient(135deg, #17324d 0%, #2f6fed 100%);
            box-shadow: 0 14px 35px rgba(23, 50, 77, 0.18);
            margin-bottom: 1.5rem;
        }

        .prio-hero h1 {
            color: white;
            margin: 0;
        }

        .prio-hero p {
            color: #e8efff;
            font-size: 1.05rem;
            margin: 0.7rem 0 0;
        }

        /* Texto secundario utilizado en explicaciones breves. */
        .prio-muted {
            color: var(--prio-muted);
        }

        /* Hacemos que los botones principales tengan bordes suaves. */
        .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 10px;
            font-weight: 650;
        }

        /* Ocultamos elementos de Streamlit que no aportan valor a la demo. */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_admin_navigation() -> None:
    """Muestra el menú en español del panel interno."""

    with st.sidebar:
        st.markdown("## ⚡ PRIO")
        st.caption("Panel interno")

        st.page_link(
            "app.py",
            label="Inicio",
            icon="🏠",
            use_container_width=True,
        )

        st.page_link(
            "pages/1_Review.py",
            label="Revisión",
            icon="✅",
            use_container_width=True,
        )

        st.page_link(
        "pages/5_Inboxes.py",
        label="Bandejas",
        icon="📥",
        use_container_width=True,
        )

        st.page_link(
            "pages/2_History.py",
            label="Historial",
            icon="🗂️",
            use_container_width=True,
        )

        st.page_link(
            "pages/3_Metrics.py",
            label="Métricas",
            icon="📊",
            use_container_width=True,
        )

        st.page_link(
            "pages/4_Settings.py",
            label="Configuración",
            icon="⚙️",
            use_container_width=True,
        )

