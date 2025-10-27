# --------------------------------------------------------------------------------
# ativos.py (Módulo da Página de Gestão de Ativos - Placeholder)
#
# Autor: Emerson A. Silva
# Data: 23/10/2025
#
# Descrição:
# Placeholder para a futura página de gestão de ativos.
# Inclui verificações de login e permissão.
# --------------------------------------------------------------------------------

import streamlit as st
import database as db


def show_ativos_page(conn):
    """Renderiza a página placeholder para Gestão de Ativos."""

    # --- Bloco de Guarda ---
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.error("Por favor, faça o login para aceder a esta página.")
        st.stop()

    user_info = st.session_state.get("user_info", {})

    # Verifica permissão usando o nome técnico da página
    if not db.check_page_access(conn, "page_ativos", user_info.get("permission_level")):
        st.error("Você não tem permissão para aceder a esta página.")
        st.stop()
    # --- Fim do Bloco de Guarda ---

    st.header("Gestão de Ativos")
    st.image(
        "https://images.unsplash.com/photo-1517430816045-df4b7de11d1d?ixlib=rb-1.2.1&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=1080&fit=max",
        caption="[Imagem de Computadores numa Mesa]")  # Placeholder visual
    st.info("Esta página está em desenvolvimento.", icon="🚧")
    st.markdown("Em breve, aqui poderá gerir outros ativos de TI da empresa.")
