# --------------------------------------------------------------------------------
# page_permissoes.py (Módulo da Página de Gerenciamento de Permissões)
#
# Autor: Emerson A. Silva
# Data: 17/10/2025
#
# Descrição:
# Página de administração para controlar o acesso de diferentes níveis de
# permissão (admin, técnico, padrão) a cada página do sistema.
# --------------------------------------------------------------------------------

import streamlit as st
import database as db

def show_permissoes_page(conn):
    """Renderiza a página para gerenciar as permissões de acesso às páginas."""

    # --- Verificação de Permissão ---
    user_info = st.session_state.get("user_info", {})
    if user_info.get("permission_level") != "admin":
        st.error("Acesso negado. Apenas administradores podem gerenciar permissões.")
        st.stop()

    st.header("Gerenciamento de Permissões de Página")
    st.info("Controle aqui qual nível de usuário pode acessar cada página do sistema. As alterações são salvas automaticamente.", icon="ℹ️")

    admin_id = user_info.get("id")
    permissions_df = db.get_all_page_permissions(conn)

    if permissions_df.empty:
        st.warning("Nenhuma regra de permissão encontrada no banco de dados.")
        st.stop()

    st.divider()

    # Mapeia os nomes técnicos das páginas para nomes amigáveis
    page_display_names = {
        "page_home": "Dashboard",
        "page_perfil": "Meu Perfil",
        "page_setores": "Gerenciar Setores",
        "page_permissoes": "Gerenciar Permissões",
        "page_gerenciamento": "Gerenciar Usuários",
        "page_logs": "Gerenciar Logs",
        "page_personalizacao": "Personalizar"
    }

    # Agrupa as permissões por página para exibição
    for page_name, group in permissions_df.groupby('page_name'):
        display_name = page_display_names.get(page_name, page_name)
        st.subheader(display_name)
        
        cols = st.columns(len(group))
        
        # Ordena para garantir que os níveis apareçam sempre na mesma ordem (admin, padrão, técnico)
        sorted_group = group.sort_values('permission_level')

        for i, row in enumerate(sorted_group.itertuples()):
            with cols[i]:
                # Cria um toggle para cada regra de permissão
                current_access = bool(row.can_access)
                new_access = st.toggle(
                    label=f"Acesso para **{row.permission_level.capitalize()}**",
                    value=current_access,
                    key=f"toggle_{page_name}_{row.permission_level}"
                )
                
                # Se o valor do toggle mudou, atualiza no banco de dados
                if new_access != current_access:
                    success, message = db.update_page_permission(
                        conn, 
                        page_name, 
                        row.permission_level, 
                        new_access, 
                        admin_id
                    )
                    
                    if success:
                        st.toast(message, icon="✔️")
                        # O st.rerun() é importante para garantir que o estado do toggle seja consistente
                        st.rerun() 
                    else:
                        st.error(message)
        
        st.divider()
