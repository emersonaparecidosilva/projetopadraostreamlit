# --------------------------------------------------------------------------------
# page_home.py (Módulo da Página Inicial - Dashboard)
#
# Autor: Emerson A. Silva
# Data: 20/10/2025
#
# Descrição:
# Dashboard com layout de cards aprimorado, exibindo os níveis de
# toner de forma mais organizada e removendo campos não utilizados.
# --------------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import database as db
import network_utils as net
import time
from datetime import datetime

def show_home_page(conn):
    """Renderiza o dashboard de monitoramento de impressoras."""
    st.header("Dashboard de Monitoramento de Impressoras")

    # --- Lógica de Atualização (Automática e Manual) ---
    REFRESH_INTERVAL_SECONDS = 300 # 5 minutos

    if 'unidade_filter' not in st.session_state:
        st.session_state.unidade_filter = "Todas"
    if 'status_filter' not in st.session_state:
        st.session_state.status_filter = "Todos"
    if 'last_check_time' not in st.session_state:
        st.session_state.last_check_time = 0
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False

    time_since_last_check = time.time() - st.session_state.last_check_time
    
    force_check = st.button("🔄 Forçar Verificação de Status", use_container_width=True)
    initial_check = (st.session_state.last_check_time == 0)
    auto_refresh_due = (st.session_state.auto_refresh and time_since_last_check > REFRESH_INTERVAL_SECONDS)

    if force_check or initial_check or auto_refresh_due:
        show_ui = not auto_refresh_due 
        all_printers_df = db.get_all_printers(conn)
        if not all_printers_df.empty:
            online, total = net.update_all_printers_status(conn, all_printers_df, show_spinner=show_ui)
            if force_check:
                st.success(f"Verificação concluída! {online} de {total} impressoras estão online.")
        
        st.session_state.last_check_time = time.time()
        st.rerun()

    st.divider()

    printers_df = db.get_all_printers(conn)
    if printers_df.empty:
        st.info("Nenhuma impressora cadastrada.")
        st.stop()

    printers_df = printers_df.sort_values(by=['status', 'nome'], ascending=[True, True])

    # --- Filtros e Toggle de Auto-Refresh ---
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write("**Filtrar por Unidade:**")
        unidades_options = ["Todas"] + sorted(printers_df['unidade'].unique())
        cols_unidade = st.columns(len(unidades_options))
        for i, unidade in enumerate(unidades_options):
            with cols_unidade[i]:
                is_active = (st.session_state.unidade_filter == unidade)
                if st.button(unidade, key=f"un_{unidade}", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.unidade_filter = unidade
                    st.rerun()
    with col2:
        st.write("**Filtrar por Status:**")
        status_options = ["Todos", "Offline", "Online"]
        cols_status = st.columns(len(status_options))
        for i, status in enumerate(status_options):
            with cols_status[i]:
                is_active = (st.session_state.status_filter == status)
                if st.button(status, key=f"st_{status}", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.status_filter = status
                    st.rerun()
    with col3:
        st.write(" ") # Espaçamento
        st.toggle('Atualização Automática', key='auto_refresh', help=f"Atualiza os dados a cada {REFRESH_INTERVAL_SECONDS // 60} minutos.")

    # --- Aplicação dos Filtros ---
    filtered_df = printers_df.copy()
    if st.session_state.unidade_filter != "Todas":
        filtered_df = filtered_df[filtered_df['unidade'] == st.session_state.unidade_filter]
    if st.session_state.status_filter != "Todos":
        filtered_df = filtered_df[filtered_df['status'] == st.session_state.status_filter]

    st.divider()
    
    # --- Exibição dos Cards Detalhados ---
    st.subheader("Impressoras Encontradas")
    if filtered_df.empty:
        st.info("Nenhuma impressora encontrada com os filtros selecionados.")
    else:
        num_columns = 3
        cols = st.columns(num_columns)
        for i, row in enumerate(filtered_df.itertuples()):
            col_index = i % num_columns
            with cols[col_index]:
                with st.container(border=True):
                    status_icon = "🟢" if getattr(row, 'status', 'Offline') == "Online" else "🔴"
                    st.markdown(f"**{getattr(row, 'nome', 'N/A')}** {status_icon}")
                    st.caption(f"Patrimônio: {getattr(row, 'patrimonio', 'N/A')} | IP: {getattr(row, 'endereco_ip', 'N/A')}")
                    st.caption(f"Local: {getattr(row, 'localizacao', 'N/A')} / {getattr(row, 'setor', 'N/A')}")

                    # --- EXIBIÇÃO DOS DADOS IPP COM LAYOUT MELHORADO ---
                    if getattr(row, 'status', 'Offline') == "Online":
                        # 1. Monta a lista de toners disponíveis
                        toner_strings = []
                        if getattr(row, 'toner_preto', -1) >= 0: toner_strings.append(f"⚫ K: {row.toner_preto}%")
                        if getattr(row, 'toner_ciano', -1) >= 0: toner_strings.append(f"🔵 C: {row.toner_ciano}%")
                        if getattr(row, 'toner_magenta', -1) >= 0: toner_strings.append(f"🟣 M: {row.toner_magenta}%")
                        if getattr(row, 'toner_amarelo', -1) >= 0: toner_strings.append(f"🟡 Y: {row.toner_amarelo}%")

                        # 2. Exibe os toners em pares (2 por linha)
                        if toner_strings:
                            for j in range(0, len(toner_strings), 2):
                                pair = toner_strings[j:j+2]
                                st.caption(" | ".join(pair))

                        # Contagem de Páginas
                        contagem = getattr(row, 'contagem_paginas', -1)
                        if contagem is not None and contagem >= 0:
                            st.caption(f"Contador: {contagem:,}".replace(",", "."))
                    
                    # A mensagem de status detalhado foi removida do card.
                    
                    # Data da Última Verificação
                    ultima_verificacao = getattr(row, 'ultima_verificacao', None)
                    if ultima_verificacao and pd.notna(ultima_verificacao):
                        last_check_str = pd.to_datetime(ultima_verificacao).strftime('%d/%m %H:%M')
                        st.caption(f"Verificado em: {last_check_str}")
                    
                    st.link_button("Acessar Web Page", f"http://{getattr(row, 'endereco_ip', '')}", use_container_width=True)

