# --------------------------------------------------------------------------------
# page_logs.py (Módulo da Página de Visualização de Logs)
#
# Autor: Emerson A. Silva
# Data: 17/10/2025
#
# Descrição:
# Página de administração para visualizar, filtrar e exportar a trilha
# de auditoria do sistema.
# --------------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import database as db
from datetime import datetime, time

def show_logs_page(conn):
    """Renderiza a página para visualizar e filtrar a trilha de auditoria."""

    st.header("Auditoria")

    logs_df = db.get_all_logs(conn)

    if logs_df.empty:
        st.info("Nenhum registro de log encontrado.")
        st.stop()
    
    if not pd.api.types.is_datetime64_any_dtype(logs_df['Data e Hora']):
        logs_df['Data e Hora'] = pd.to_datetime(logs_df['Data e Hora'])

    # --- Filtros ---
    
    col1, col2, col3 = st.columns(3)

    with col1:
        user_list = ["Todos"] + sorted(logs_df['Nome do Usuário'].dropna().unique())
        selected_user = st.selectbox("Filtrar por Usuário:", user_list)

    with col2:
        action_list = ["Todos"] + sorted(logs_df['Tipo de Ação'].unique())
        selected_action = st.selectbox("Filtrar por Ação:", action_list)
        
    with col3:
        min_date = logs_df['Data e Hora'].min().date()
        max_date = logs_df['Data e Hora'].max().date()
        date_range = st.date_input(
            "Filtrar por Período:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    # --- Aplicação dos Filtros ---
    filtered_df = logs_df.copy()

    if selected_user != "Todos":
        filtered_df = filtered_df[filtered_df['Nome do Usuário'] == selected_user]
    
    if selected_action != "Todos":
        filtered_df = filtered_df[filtered_df['Tipo de Ação'] == selected_action]

    if len(date_range) == 2:
        start_date, end_date = date_range
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)
        filtered_df = filtered_df[
            (filtered_df['Data e Hora'] >= start_datetime) & 
            (filtered_df['Data e Hora'] <= end_datetime)
        ]

    st.divider()

    # --- Botão de Exportação e Contagem de Registros ---
    col_info, col_export = st.columns([3, 1])
    
    with col_info:
        st.subheader(f"Exibindo {len(filtered_df)} de {len(logs_df)} registros")

    with col_export:
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar para CSV",
                data=csv,
                file_name=f'logs_filtrados_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
                use_container_width=True
            )

    # --- Exibição dos Logs ---
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

