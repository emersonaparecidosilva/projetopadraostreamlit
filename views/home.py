import streamlit as st
import database as db


def show_home_page(conn):
    """Renderiza o dashboard de monitoramento de impressoras."""
    st.header("Bem vindo ao Sistema Padrão")

    