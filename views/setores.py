# --------------------------------------------------------------------------------
# page_setores.py (Módulo da Página de Gerenciamento de Setores)
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

# --- Listas de Opções para Padronização ---
TORRE_OPTIONS = ["Torre 1", "Torre 2", "Outro"]
ANDAR_OPTIONS = ["Térreo"] + [f"{i}º Andar" for i in range(1, 18)] + ["Outro"]

def show_setores_page(conn):
    """Renderiza a página completa para gerenciamento de setores."""

    # A verificação de permissão foi removida daqui, pois o app.py
    # agora controla o acesso a esta página dinamicamente.

    st.header("Gerenciamento de Setores")
    
    # É seguro pegar o user_info aqui, pois a página só é acessível se o usuário estiver logado.
    user_info = st.session_state.get("user_info", {})
    admin_id = user_info.get("id")

    # --- Formulário para Adicionar Novo Setor ---
    with st.expander("➕ Adicionar Novo Setor"):
        with st.form("new_sector_form", clear_on_submit=False):
            data = {}
            col1, col2 = st.columns(2)
            with col1:
                data['location_tower'] = st.selectbox("Torre", TORRE_OPTIONS, key="add_tower")
                data['location_floor'] = st.selectbox("Andar", ANDAR_OPTIONS, key="add_floor")
                data['sector_name'] = st.text_input("Nome do Setor *")
                data['cost_center'] = st.text_input("Centro de Custo (apenas números)")
            with col2:
                data['manager_name'] = st.text_input("Nome do Gestor")
                data['manager_contact'] = st.text_input("Contato do Gestor (Telefone/Email)")

            submitted = st.form_submit_button("Adicionar Setor", use_container_width=True)
            if submitted:
                if not data['sector_name']:
                    st.warning("O campo 'Nome do Setor' é obrigatório.")
                elif data['cost_center'] and not data['cost_center'].isdigit():
                    st.warning("O campo 'Centro de Custo' deve conter apenas números.")
                else:
                    success, message = db.add_sector(conn, data, admin_id)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    st.divider()

    # --- Busca e Lista de Setores ---
    sectors_df = db.get_all_sectors(conn, only_active=False) 
    if sectors_df.empty:
        st.info("Nenhum setor cadastrado.")
        st.stop()
    
    st.subheader("Busca e Exportação")
    
    col_search, col_export = st.columns([3, 1])

    with col_search:
        search_term = st.text_input("🔎 Buscar setor:")
    
    if search_term:
        mask = sectors_df.apply(lambda row: any(search_term.lower() in str(cell).lower() for cell in row), axis=1)
        filtered_df = sectors_df[mask]
    else:
        filtered_df = sectors_df

    with col_export:
        if not filtered_df.empty:
            st.write("") 
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Exportar para CSV",
                data=csv,
                file_name='lista_setores.csv',
                mime='text/csv',
                use_container_width=True
            )

    st.divider()
    st.subheader("Lista de Setores Cadastrados")

    if filtered_df.empty:
        st.warning("Nenhum setor encontrado com o critério de busca.")
    else:
        for index, sector in filtered_df.iterrows():
            sector_id_int = int(sector['id'])
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.subheader(sector['sector_name'])
                    st.caption(f"Local: {sector['location_tower']} - {sector['location_floor']} | CC: {sector.get('cost_center', 'N/A')}")
                with col2:
                    st.text(f"Gestor: {sector.get('manager_name', 'N/A')}")
                    st.text(f"Contato: {sector.get('manager_contact', 'N/A')}")
                with col3:
                    status_color = "🟢" if sector['status'] == 'ativo' else "🔴"
                    st.text(f"Status: {status_color} {sector['status'].capitalize()}")

                    btn_col1, btn_col2 = st.columns(2)
                    if btn_col1.button("✏️ Editar", key=f"edit_{sector_id_int}", use_container_width=True):
                        st.session_state['edit_sector_id'] = sector_id_int
                        st.rerun()

                    new_status = 'inativo' if sector['status'] == 'ativo' else 'ativo'
                    btn_text = "🔴 Inativar" if sector['status'] == 'ativo' else "🟢 Ativar"
                    if btn_col2.button(btn_text, key=f"status_{sector_id_int}", use_container_width=True):
                        success, message = db.update_sector_status(conn, sector_id_int, sector['sector_name'], new_status, admin_id)
                        if success:
                            st.toast(message, icon="✔️")
                            st.rerun()
                        else:
                            st.error(message)
            
            # --- Formulário de Edição ---
            if st.session_state.get('edit_sector_id') == sector_id_int:
                with st.expander(f"Editando {sector['sector_name']}", expanded=True):
                    with st.form(key=f"form_edit_{sector_id_int}"):
                        edit_data = {}
                        c1, c2 = st.columns(2)
                        with c1:
                            torre_idx = TORRE_OPTIONS.index(sector['location_tower']) if sector['location_tower'] in TORRE_OPTIONS else 0
                            edit_data['location_tower'] = st.selectbox("Torre ", TORRE_OPTIONS, index=torre_idx, key=f"torre_edit_{sector_id_int}")

                            andar_idx = ANDAR_OPTIONS.index(sector['location_floor']) if sector['location_floor'] in ANDAR_OPTIONS else 0
                            edit_data['location_floor'] = st.selectbox("Andar ", ANDAR_OPTIONS, index=andar_idx, key=f"andar_edit_{sector_id_int}")
                            
                            edit_data['sector_name'] = st.text_input("Nome do Setor *", value=sector['sector_name'], key=f"name_edit_{sector_id_int}")
                            edit_data['cost_center'] = st.text_input("Centro de Custo", value=sector.get('cost_center', ''), key=f"cc_edit_{sector_id_int}")
                        with c2:
                            edit_data['manager_name'] = st.text_input("Nome do Gestor", value=sector.get('manager_name', ''), key=f"gestor_edit_{sector_id_int}")
                            edit_data['manager_contact'] = st.text_input("Contato do Gestor", value=sector.get('manager_contact', ''), key=f"contato_edit_{sector_id_int}")

                        btn_save, btn_cancel = st.columns(2)
                        if btn_save.form_submit_button("Salvar Alterações", use_container_width=True):
                            if not edit_data['sector_name']:
                                st.warning("O campo 'Nome do Setor' é obrigatório.")
                            elif edit_data['cost_center'] and not edit_data['cost_center'].isdigit():
                                st.warning("O campo 'Centro de Custo' deve conter apenas números.")
                            else:
                                success, message = db.update_sector(conn, sector_id_int, edit_data, admin_id)
                                if success:
                                    st.success(message)
                                    del st.session_state['edit_sector_id']
                                    st.rerun()
                                else:
                                    st.error(message)
                        
                        if btn_cancel.form_submit_button("Cancelar", type="secondary", use_container_width=True):
                            del st.session_state['edit_sector_id']
                            st.rerun()

