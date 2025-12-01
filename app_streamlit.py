# app_streamlit.py
import json
import streamlit as st

# 🔗 IMPORTAMOS EL MODELO
from gemini_model import generate_insights


# ---------------------------
# Estilos globales (CSS)
# ---------------------------
def inject_global_css():
    st.markdown(
        """
        <style>
        /* Fondo general oscuro */
        [data-testid="stAppViewContainer"] {
            background: #020617;  /* casi negro, azul muy oscuro */
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #020617;
            border-right: 1px solid #111827;
        }

        [data-testid="stSidebar"] * {
            color: #e5e7eb;
        }

        /* Títulos principales */
        h1, h2, h3, h4 {
            color: #f9fafb;
        }

        /* Texto normal */
        .main-content, .main-content p {
            color: #e5e7eb;
        }

        /* Navegación (radio horizontal) */
        [data-testid="stRadio"] > div {
            flex-direction: row;
            justify-content: center;
            gap: 0.75rem;
        }

        [data-testid="stRadio"] label {
            background: transparent;
            padding: 0.25rem 1.2rem;
            border-radius: 999px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            color: #e5e7eb;
            font-weight: 500;
        }

        [data-testid="stRadio"] label:hover {
            background: #111827;
        }

        [data-testid="stRadio"] input:checked + div {
            border-bottom: 2px solid #ef4444; /* rojo para la pestaña activa */
            color: #fef2f2;
        }

        /* Cartas de características */
        .feature-card {
            border-radius: 12px;
            padding: 1rem 1.25rem;
            background: #020617;
            border: 1px solid #111827;
            box-shadow: 0 18px 30px rgba(0,0,0,0.45);
        }

        .feature-card h3 {
            margin-top: 0;
            margin-bottom: 0.5rem;
        }

        .feature-card p {
            margin-bottom: 0;
            font-size: 0.9rem;
        }

        /* Texto secundario */
        .muted {
            color: #9ca3af;
            font-size: 0.9rem;
        }

        /* Subrayado rojo fino bajo el título principal */
        .title-underline {
            width: 90px;
            height: 3px;
            background: #ef4444;
            border-radius: 999px;
            margin-top: 0.4rem;
            margin-bottom: 1.2rem;
        }

        /* Links azules en sidebar */
        .sidebar-link a {
            color: #60a5fa !important;
            text-decoration: none;
        }
        .sidebar-link a:hover {
            text-decoration: underline;
        }

        /* Caja de chat: que se vea integrada */
        .stChatInputContainer {
            border-top: 1px solid #111827;
            background: #020617;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------
# Sidebar
# ---------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown("### Copilot DN 🤖")
        st.markdown(
            "Plataforma para explorar insights de empleo y eventos "
            "en Perú, potenciados con IA."
        )

        st.markdown("---")

        st.markdown("#### 🌐 Conéctate con nosotros")
        st.markdown(
            "- [Visita nuestra página web](https://tu-sitio.com)\n"
            "- Escríbenos para una demo personalizada."
        )

        st.markdown("---")

        st.markdown("#### 📬 Buzón de Mensajes")

        with st.expander("Noticias y eventos", expanded=True):
            st.markdown(
                "Aquí aparecerán las noticias actualizadas y eventos lanzados.\n\n"
                "_Funcionalidad en desarrollo._ 😄"
            )

        st.markdown("---")

        st.markdown("**Enlaces adicionales:**")
        st.markdown(
            '<div class="sidebar-link">• '
            '<a href="https://tu-sitio.com" target="_blank">Página web oficial</a>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sidebar-link">• '
            '<a href="https://www.linkedin.com" target="_blank">LinkedIn</a></div>',
            unsafe_allow_html=True,
        )


# ---------------------------
# Secciones principales
# ---------------------------
def render_tab_explorar():
    st.markdown(
        "<div class='main-content'>"
        "<h1 style='margin-bottom:0;'>Explorar Copilot-DN</h1>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='title-underline'></div>", unsafe_allow_html=True)

    st.markdown(
        "<p class='main-content' style='font-size:1.05rem;'>"
        "Descubre las funcionalidades clave de Copilot DN."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p class='muted'>"
        "Revisar la Guía de Usuario en la sección "
        "<b>💡 Cómo usar</b> antes de probar Copilot DN."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🔍 Exploración de empleo</h3>
                <p>
                    Analiza vacantes recientes en plataformas como LinkedIn
                    y descubre qué perfiles están siendo más demandados.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🎟️ Eventos y formación</h3>
                <p>
                    Mantente al tanto de bootcamps, webinars y eventos
                    relacionados al desarrollo profesional en Perú.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🤖 IA para insights</h3>
                <p>
                    Copilot DN resume la información y te entrega
                    recomendaciones accionables para tu empleabilidad.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown(
        "<p class='muted'>"
        "Cuando el modelo esté conectado podrás hacer preguntas como: "
        "<i>“¿Qué sectores tienen más demanda en Lima esta semana?”</i>."
        "</p>",
        unsafe_allow_html=True,
    )


def render_tab_como_usar():
    st.markdown(
        "<div class='main-content'>"
        "<h1 style='margin-bottom:0;'>Cómo usar Copilot-DN</h1>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='title-underline'></div>", unsafe_allow_html=True)

    st.markdown(
        """
        1. **Carga de datos**  
           Ejecuta los módulos de scraping para obtener:
           - Ofertas de empleo recientes (LinkedIn u otras fuentes).
           - Eventos y actividades de formación (Ticketmaster, Eventbrite, etc.).

        2. **Generación de insights**  
           El modelo IA (Gemini) analizará automáticamente:
           - Sectores con mayor demanda.
           - Habilidades más solicitadas.
           - Eventos relevantes para tu perfil.

        3. **Interacción con Copilot**  
           Desde la pestaña **🤖 Copilot DN** podrás hacer preguntas en lenguaje natural
           y recibir respuestas estructuradas y accionables.
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown("#### Recomendaciones de uso")

    st.markdown(
        """
        - Mantén los datos actualizados ejecutando los scrapers de forma periódica.  
        - Formula preguntas concretas para obtener mejores respuestas (ej.:  
          _“¿Qué habilidades piden más para roles de data analyst en Lima?”_).  
        - Usa los resultados para actualizar tu CV, LinkedIn o plan de capacitación.
        """
    )


def render_tab_copilot():
    st.markdown(
        "<div class='main-content'>"
        "<h1 style='margin-bottom:0;'>Copilot DN</h1>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='title-underline'></div>", unsafe_allow_html=True)

    st.markdown(
        """
        Esta sección será tu espacio principal para conversar con el asistente.

        Ya puedes hacer preguntas y Copilot DN responderá usando los datos cargados
        desde LinkedIn y los eventos (si Redis y los scrapers están correctamente configurados).
        """
    )

    st.markdown("---")

    st.markdown("#### Ejemplos de preguntas")

    st.markdown(
        """
        - *“¿Qué sectores tienen más ofertas hoy en Perú?”*  
        - *“Recomiéndame 3 eventos útiles para mejorar mi perfil en data.”*  
        - *“¿Qué habilidades blandas se repiten más en las ofertas recientes?”*
        """
    )

    st.markdown("---")

    # ---------------------------
    # HISTORIAL DE CHAT EN SESIÓN
    # ---------------------------
    if "chat_history" not in st.session_state:
        # Cada elemento: {"role": "user" | "assistant", "content": "texto"}
        st.session_state["chat_history"] = []

    # Botón para borrar conversación
    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("🧹 Borrar conversación"):
            st.session_state["chat_history"] = []
            st.experimental_rerun()

    st.markdown("")

    # Pintamos todo el historial previo
    for turn in st.session_state["chat_history"]:
        if turn["role"] == "user":
            with st.chat_message("user"):
                st.markdown(turn["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(turn["content"])

    # Entrada de chat (parte inferior)
    user_prompt = st.chat_input("Hazme una pregunta...")

    if user_prompt:
        # 1) mostramos mensaje del usuario y lo guardamos
        st.session_state["chat_history"].append(
            {"role": "user", "content": user_prompt}
        )
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # 2) llamamos al modelo con historial
        with st.chat_message("assistant"):
            with st.spinner("Analizando datos y generando insights con Copilot DN..."):
                try:
                    result = generate_insights(
                        user_question=user_prompt,
                        history=st.session_state["chat_history"],
                    )
                except Exception as e:
                    st.error(f"Ocurrió un error al llamar al modelo: {e}")
                    return

                # 3) convertimos dict JSON a texto bonito si hace falta
                if isinstance(result, dict):
                    assistant_text = json.dumps(
                        result, indent=2, ensure_ascii=False
                    )
                else:
                    assistant_text = str(result)

                st.markdown(assistant_text)

        # 4) guardamos la respuesta en historial
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": assistant_text}
        )


# ---------------------------
# App principal
# ---------------------------
def main():
    st.set_page_config(
        page_title="Copilot DN",
        page_icon="🤖",
        layout="wide",
    )

    inject_global_css()
    render_sidebar()

    # Navegación superior tipo pestañas
    tab = st.radio(
        "Navegación",
        ["🔓 Explorar", "💡 Cómo usar", "🤖 Copilot DN"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("")  # pequeño espacio

    if "Explorar" in tab:
        render_tab_explorar()
    elif "Cómo usar" in tab:
        render_tab_como_usar()
    else:
        render_tab_copilot()


if __name__ == "__main__":
    main()
