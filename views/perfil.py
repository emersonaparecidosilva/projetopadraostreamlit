# --------------------------------------------------------------------------------
# perfil.py (Módulo da Página de Perfil do Usuário)
#
# Autor: Emerson A. Silva
# Data: 22/10/2025
#
# Descrição:
# Versão corrigida para atualizar o 'force_password_change' na session_state
# após a alteração bem-sucedida da senha, liberando o acesso ao sistema.
# --------------------------------------------------------------------------------

import streamlit as st
import database as db
import re


# --- FUNÇÃO DE VALIDAÇÃO DE SENHA ---
def is_password_strong(password):
    """Verifica se a senha atende aos critérios de segurança."""
    if len(password) < 8:
        return (False, "A senha deve ter no mínimo 8 caracteres.")
    if not re.search(r"[a-zA-Z]", password):
        return (False, "A senha deve conter letras.")
    if not re.search(r"[0-9]", password):
        return (False, "A senha deve conter números.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return (False, "A senha deve conter ao menos um caractere especial (ex: !@#$).")
    return (True, "OK")


def show_perfil_page(conn):
    """Renderiza a página para o utilizador alterar a própria senha."""

    user_info = st.session_state.get("user_info")
    if not user_info:
        st.error("Não foi possível carregar as informações do utilizador. Por favor, faça o login novamente.")
        st.stop()  # Interrompe se não houver user_info

    st.header("Meu Perfil")

    # Verifica se a senha precisa ser alterada e mostra o aviso
    must_change_password = st.session_state.get("force_password_change", False)
    if must_change_password:
        st.warning("É necessário definir uma nova senha antes de poder aceder a outras páginas.", icon="🔒")
    else:
        st.write(f"Olá, **{user_info.get('name', 'Utilizador')}**. Use o formulário abaixo para alterar sua senha.")

    # --- Formulário de Alteração de Senha ---
    with st.form("change_password_form"):  # clear_on_submit=False é melhor aqui
        st.write("### Alterar Senha")
        old_password = st.text_input("Senha Antiga *", type="password")
        new_password = st.text_input("Nova Senha *", type="password")
        confirm_password = st.text_input("Confirme a Nova Senha *", type="password")

        submitted = st.form_submit_button("Salvar Nova Senha", use_container_width=True)

        if submitted:
            is_strong, strength_message = is_password_strong(new_password)

            if not all([old_password, new_password, confirm_password]):
                st.warning("Por favor, preencha todos os campos.")
            elif new_password != confirm_password:
                st.error("A nova senha e a confirmação não coincidem.")
            elif not is_strong:
                st.error(f"Nova senha é fraca: {strength_message}")
            else:
                user_id = user_info['id']

                success, message = db.update_user_password(conn, user_id, old_password, new_password, user_id)

                if success:
                    st.success(message)
                    # --- CORREÇÃO AQUI ---
                    # Atualiza a flag na session_state imediatamente
                    st.session_state["force_password_change"] = False
                    st.info("Senha atualizada! A recarregar...")
                    st.rerun()  # Força o recarregamento para liberar o acesso
                else:
                    st.error(message)
