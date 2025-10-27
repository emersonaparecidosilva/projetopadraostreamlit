# --------------------------------------------------------------------------------
# page_impressoras.py (Módulo da Página de Gerenciamento de Impressoras)
#
# Autor: Emerson A. Silva
# Data: 17/10/2025
#
# Descrição:
# Versão final com a verificação de permissão removida, centralizando
# a lógica de segurança no app.py.
# --------------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import database as db
import re

# --- Listas de Opções Fixas ---
UNIDADES_OPTIONS = ["Barueri", "Araçariguama"]
FABRICANTES_OPTIONS = ['HP', 'Xerox', 'Canon', 'Brother', 'Epson']

def is_valid_ip(ip):
    """Valida se a string está em um formato de IP válido."""
    if not ip: return False
    pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    return pattern.match(ip)

def show_impressoras_page(conn):
    """Renderiza a página para adicionar e editar impressoras com dados dinâmicos."""
    
    # A verificação de permissão foi removida daqui, pois o app.py
    # agora controla o acesso a esta página dinamicamente.

    st.header("Gerenciamento de Impressoras")
    
    user_info = st.session_state.get("user_info", {})
    admin_id = user_info.get("id")

    # --- Carrega os setores ativos do banco de dados ---
    sectors_df = db.get_all_sectors(conn, only_active=True)
    active_sectors_list = []
    if not sectors_df.empty:
        active_sectors_list = sectors_df['sector_name'].tolist()

    # --- Formulário para Adicionar Nova Impressora ---
    with st.expander("➕ Adicionar Nova Impressora"):
        if not active_sectors_list:
            st.warning("Nenhum setor ativo encontrado. Por favor, cadastre um setor antes de adicionar uma impressora.")
        else:
            with st.form("new_printer_form", clear_on_submit=False):
                data = {}
                col1, col2 = st.columns(2)
                with col1:
                    data['unidade'] = st.selectbox("Unidade", UNIDADES_OPTIONS)
                    data['fabricante'] = st.selectbox("Fabricante", FABRICANTES_OPTIONS)
                    data['modelo'] = st.text_input("Modelo")
                    data['setor'] = st.selectbox("Setor *", active_sectors_list)
                with col2:
                    data['patrimonio'] = st.text_input("Patrimônio * (apenas números)")
                    data['nome'] = st.text_input("Nome/Apelido *")
                    data['host'] = st.text_input("Hostname")
                    data['endereco_ip'] = st.text_input("Endereço IP *", placeholder="Ex: 192.168.0.1")
                
                submitted = st.form_submit_button("Adicionar Impressora", use_container_width=True)
                if submitted:
                    errors = []
                    if not all([data.get('patrimonio'), data.get('nome'), data.get('endereco_ip')]):
                        errors.append("Os campos com * são obrigatórios.")
                    if data.get('patrimonio') and not data.get('patrimonio', '').isdigit():
                        errors.append("O campo 'Patrimônio' deve conter apenas números.")
                    if data.get('endereco_ip') and not is_valid_ip(data.get('endereco_ip')):
                        errors.append("O formato do 'Endereço IP' é inválido.")
                    
                    if errors:
                        for error in errors:
                            st.warning(error)
                    else:
                        selected_sector_info = sectors_df[sectors_df['sector_name'] == data['setor']].iloc[0]
                        data['localizacao'] = f"{selected_sector_info['location_tower']} - {selected_sector_info['location_floor']}"

                        success, message = db.add_printer(conn, data, admin_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

    st.divider()

    printers_df = db.get_all_printers(conn)
    if printers_df.empty:
        st.info("Nenhuma impressora cadastrada.")
        st.stop()

    search_term = st.text_input("🔎 Buscar impressora (por nome, patrimônio, setor, etc.):")
    
    if search_term:
        mask = printers_df.apply(lambda row: any(search_term.lower() in str(cell).lower() for cell in row), axis=1)
        filtered_df = printers_df[mask]
    else:
        filtered_df = printers_df
    
    if not filtered_df.empty:
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar para CSV", csv, "lista_impressoras.csv", "text/csv")

    st.subheader("Lista de Impressoras Cadastradas")

    if filtered_df.empty:
        st.warning("Nenhuma impressora encontrada com o critério de busca.")
    else:
        for index, printer in filtered_df.iterrows():
            printer_id_int = int(printer['id'])
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.subheader(printer.get('nome', 'N/A'))
                    st.caption(f"Patrimônio: {printer.get('patrimonio', 'N/A')} | IP: {printer.get('endereco_ip', 'N/A')}")
                with col2:
                    st.text(f"Localização: {printer.get('localizacao', 'N/A')}")
                    st.text(f"Setor: {printer.get('setor', 'N/A')}")
                with col3:
                    status_color = "🟢" if printer.get('status') == 'Online' else "🔴"
                    st.text(f"Status: {status_color} {printer.get('status', 'Desconhecido')}")
                    if st.button("✏️ Editar", key=f"edit_{printer_id_int}", use_container_width=True):
                        st.session_state['edit_printer_id'] = printer_id_int
                        st.rerun()

            if st.session_state.get('edit_printer_id') == printer_id_int:
                with st.expander(f"Editando {printer['nome']}", expanded=True):
                    with st.form(key=f"form_edit_{printer_id_int}"):
                        edit_data = {}
                        c1, c2 = st.columns(2)
                        with c1:
                            unidade_idx = UNIDADES_OPTIONS.index(printer['unidade']) if printer['unidade'] in UNIDADES_OPTIONS else 0
                            edit_data['unidade'] = st.selectbox("Unidade ", UNIDADES_OPTIONS, index=unidade_idx, key=f"unidade_{printer_id_int}")
                            
                            fab_idx = FABRICANTES_OPTIONS.index(printer['fabricante']) if printer['fabricante'] in FABRICANTES_OPTIONS else 0
                            edit_data['fabricante'] = st.selectbox("Fabricante ", FABRICANTES_OPTIONS, index=fab_idx, key=f"fab_{printer_id_int}")
                            
                            edit_data['modelo'] = st.text_input("Modelo ", value=printer.get('modelo', ''), key=f"modelo_{printer_id_int}")
                            
                            setor_idx = active_sectors_list.index(printer['setor']) if printer['setor'] in active_sectors_list else 0
                            edit_data['setor'] = st.selectbox("Setor * ", active_sectors_list, index=setor_idx, key=f"setor_{printer_id_int}")
                        with c2:
                            edit_data['patrimonio'] = st.text_input("Patrimônio * ", value=printer['patrimonio'], key=f"pat_{printer_id_int}")
                            edit_data['nome'] = st.text_input("Nome/Apelido * ", value=printer['nome'], key=f"nome_{printer_id_int}")
                            edit_data['host'] = st.text_input("Hostname ", value=printer.get('host', ''), key=f"host_{printer_id_int}")
                            edit_data['endereco_ip'] = st.text_input("Endereço IP * ", value=printer['endereco_ip'], key=f"ip_{printer_id_int}")
                        
                        btn_save, btn_cancel = st.columns(2)
                        if btn_save.form_submit_button("Salvar Alterações", use_container_width=True):
                            errors = []
                            # (validações)
                            if not all([edit_data.get('patrimonio'), edit_data.get('nome'), edit_data.get('endereco_ip')]):
                                errors.append("Os campos com * são obrigatórios.")
                            if edit_data.get('patrimonio') and not edit_data.get('patrimonio', '').isdigit():
                                errors.append("O campo 'Patrimônio' deve conter apenas números.")
                            if edit_data.get('endereco_ip') and not is_valid_ip(edit_data.get('endereco_ip')):
                                errors.append("O formato do 'Endereço IP' é inválido.")
                            
                            if errors:
                                for error in errors:
                                    st.warning(error)
                            else:
                                selected_sector_info = sectors_df[sectors_df['sector_name'] == edit_data['setor']].iloc[0]
                                edit_data['localizacao'] = f"{selected_sector_info['location_tower']} - {selected_sector_info['location_floor']}"

                                success, message = db.update_printer(conn, printer_id_int, edit_data, admin_id)
                                if success:
                                    st.success(message)
                                    del st.session_state['edit_printer_id']
                                    st.rerun()
                                else:
                                    st.error(message)
                        
                        if btn_cancel.form_submit_button("Cancelar", type="secondary", use_container_width=True):
                            del st.session_state['edit_printer_id']
                            st.rerun()

