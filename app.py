# --------------------------------------------------------------------------------
# app.py (Arquivo Principal - Roteador de Páginas)
#
# Autor: Emerson
# Data: 22/10/2025
#
# Descrição:
# Versão com botão "Esqueci a Senha" integrado ao formulário de login,
# controlando a exibição da view de reset via session_state e
# redirecionamento para troca de senha obrigatória.
# --------------------------------------------------------------------------------

import streamlit as st
from streamlit_option_menu import option_menu
import database as db
import views as v  # Usa o alias 'v' para as views

# --- Configuração da Página ---
st.set_page_config(
    page_title="Sistema de Gestão",
    page_icon="🖨️",
    layout="wide"
)

# --- Inicialização da Conexão com o Banco de Dados ---
conn = db.init_connection()


# --- Funções de Autenticação (ATUALIZADAS) ---
def login_form():
    """Exibe o formulário de login."""

    login_title = db.get_setting(conn, 'login_title') or "Login do Sistema"
    bg_base64 = db.get_setting(conn, 'login_bg_base64')

    if bg_base64:
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("{bg_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{ background-color: transparent; }}
        [data-testid="stAppViewContainer"] > .main {{ background-color: transparent; }}
        </style>
        """, unsafe_allow_html=True)

    st.header(login_title)
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="Digite seu email")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")

        # --- BOTÕES LADO A LADO ---
        # --- ALTERAÇÃO AQUI: Botões em linhas separadas ---
        # Removemos as colunas. Cada botão agora ocupa uma linha inteira.
        
        # Botão Entrar (agora vem primeiro, como é mais comum)
        submitted_login = st.form_submit_button("Entrar", use_container_width=True)
        
        # Botão Esqueci a Senha (embaixo do botão Entrar)
        if st.form_submit_button("Esqueci a Senha", type="secondary", use_container_width=True):
            st.session_state['show_reset_view'] = True
            st.rerun()
        # --- FIM DA ALTERAÇÃO ---


        if submitted_login:
            # Chama check_login sem IP/User-Agent
            user_data = db.check_login(conn, email, password)

            if user_data:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = user_data
                # Guarda o estado da flag na sessão
                st.session_state["force_password_change"] = user_data.get('force_password_change', False)
                # Garante que a view de reset seja desativada após o login
                if 'show_reset_view' in st.session_state:
                    del st.session_state['show_reset_view']
                st.rerun()
            else:
                st.error("Email ou senha incorretos. Verifique também se seu usuário está 'ativo'.")


# --- FUNÇÃO DE LOGOUT ATUALIZADA ---
def logout():
    """Realiza o logout, limpa caches e regista a ação."""
    try:
        db.get_setting.clear()
        db.get_all_settings.clear()
        user_info = st.session_state.get("user_info")
        if user_info:
            details = f"Usuário '{user_info['email']}' (ID: {user_info['id']}) efetuou logout."
            # Chama log_action sem IP/User-Agent
            db.log_action(conn, user_info['id'], 'USER_LOGOUT', details)
    except Exception as e:
        print(f"Erro durante o logout: {e}")

    # Limpa toda a sessão, incluindo 'show_reset_view' se existir
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# --- Estrutura Principal do App ---

# Inicializa o estado de controle da view de reset
if 'show_reset_view' not in st.session_state:
    st.session_state['show_reset_view'] = False

# Verifica se está logado OU se deve mostrar a view de reset
if not st.session_state.get("logged_in", False):
    if st.session_state['show_reset_view']:
        v.show_reset_page(conn)  # Chama a página de reset
    else:
        login_form()  # Mostra o formulário de login
else:
    # --- Lógica para utilizadores logados ---
    user_info = st.session_state["user_info"]
    permission_level = user_info.get("permission_level")
    # Pega o estado da flag da sessão
    must_change_password = st.session_state.get("force_password_change", False)

    # --- LÓGICA DE REDIRECIONAMENTO ---
    if must_change_password:
        selected_display_name = "Meu Perfil"  # Força a seleção do perfil
        st.warning("É necessário definir uma nova senha antes de continuar.", icon="⚠️")
    else:
        selected_display_name = None  # Deixa o menu decidir

    with st.sidebar:
        st.subheader(f"Olá, {user_info['name']}!")

        PAGE_MAP = {
            "page_home": ("Dashboard", "house-fill"),
            "page_perfil": ("Meu Perfil", "person-fill"),
            "page_impressoras": ("Gerenciar Impressoras", "printer-fill"),
            "page_setores": ("Gerenciar Setores", "buildings-fill"),
            "page_ativos": ("Gestão de Ativos", "hdd-stack-fill"),
            "page_gerenciamento": ("Gerenciar Usuários", "people-fill"),
            "page_permissoes": ("Gerenciar Permissões", "shield-lock-fill"),
            "page_logs": ("Trilha de Auditoria", "clock-history"),
            "page_personalizacao": ("Personalizar", "palette-fill")
        }
        ordered_pages = ["page_home", "page_perfil","page_ativos", "page_impressoras", "page_setores",
                         "page_gerenciamento", "page_permissoes", "page_logs",
                         "page_personalizacao"]

        menu_options = []
        icons = []
        default_index = 0

        for i, page_name in enumerate(ordered_pages):
            # Apenas mostra o menu se a senha NÃO precisar ser trocada, OU se for a página de perfil
            if (not must_change_password or page_name == "page_perfil") and db.check_page_access(conn, page_name,
                                                                                                 permission_level):
                display_name, icon = PAGE_MAP[page_name]
                menu_options.append(display_name)
                icons.append(icon)
                # Define o índice padrão se for a página de perfil E a senha precisar ser trocada
                if must_change_password and display_name == "Meu Perfil":
                    default_index = len(menu_options) - 1  # Será sempre 0 neste caso

        if menu_options:
            # Se a seleção foi forçada (must_change_password), usa o valor fixo
            # Caso contrário, permite que o option_menu determine a seleção
            if selected_display_name is None:
                selected_display_name = option_menu(
                    menu_title="Menu Principal", options=menu_options,
                    icons=icons, menu_icon="cast", default_index=default_index,
                )
        else:
            # Isso só deve acontecer se o utilizador não tiver permissão nem para o perfil
            selected_display_name = None
            st.warning("Você não tem permissão para acessar nenhuma página.")

        # Oculta o botão de logout se a senha precisar ser trocada
        if not must_change_password:
            if st.button("Sair", use_container_width=True):
                logout()

    # --- Roteamento ---
    selected_page_name = None
    for tech_name, (display_name, icon) in PAGE_MAP.items():
        if display_name == selected_display_name:
            selected_page_name = tech_name
            break

    # Chama a função da página correta
    if selected_page_name == "page_perfil":
        v.show_perfil_page(conn)
    elif must_change_password:
        # Se a senha precisa ser trocada e a página selecionada NÃO É "Meu Perfil",
        # exibe o aviso em vez de renderizar a página.
        # A página de perfil já foi tratada acima.
        st.warning("Acesso restrito. Por favor, altere sua senha na página 'Meu Perfil'.")
    elif selected_page_name == "page_home":
        v.show_home_page(conn)
    elif selected_page_name == "page_impressoras":
        v.show_impressoras_page(conn)
    elif selected_page_name == "page_setores":
        v.show_setores_page(conn)
    elif selected_page_name == "page_gerenciamento":
        v.show_gerenciamento_page(conn)
    elif selected_page_name == "page_permissoes":
        v.show_permissoes_page(conn)
    elif selected_page_name == "page_logs":
        v.show_logs_page(conn)
    elif selected_page_name == "page_personalizacao":
        v.show_personalizacao_page(conn)
    elif selected_page_name == "page_ativos":
        v.show_ativos_page(conn)
    elif selected_display_name:
        st.error("Página não encontrada.")

