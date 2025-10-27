# --------------------------------------------------------------------------------
# reset.py (Módulo da Página de Reset de Senha)
#
# Autor: Emerson A. Silva
# Data: 22/10/2025
#
# Descrição:
# Versão corrigida com a lógica adicionada ao botão "Voltar para o Login"
# para retornar corretamente à tela de login.
# --------------------------------------------------------------------------------

import streamlit as st
import database as db
from utils.email_utils import enviar_email_senha  # Importa a função de envio de email
import time


def show_reset_page(conn):
    """Renderiza a página para solicitação de reset de senha."""

    st.header("🔑 Redefinir Senha")
    st.info(
        "Insira o seu endereço de email abaixo. Se o email estiver cadastrado no sistema, enviaremos uma senha temporária para você.",
        icon="ℹ️")

    with st.form("reset_password_form"):
        email_usuario = st.text_input("Seu Email Cadastrado:", placeholder="usuario@exemplo.com")
        submitted = st.form_submit_button("Enviar Senha Temporária", use_container_width=True)

        if submitted:
            if not email_usuario:
                st.warning("Por favor, insira o seu email.")
            else:
                with st.spinner("A processar a sua solicitação..."):
                    if db.find_user_by_email(conn, email_usuario):
                        success_db, senha_ou_erro = db.reset_user_password(conn, email_usuario,
                                                                           0)  # ID 0 indica ação do próprio utilizador/sistema

                        if success_db:
                            senha_temporaria = senha_ou_erro
                            email_sent = enviar_email_senha(email_usuario, senha_temporaria)

                            if email_sent:
                                st.success(
                                    "Sucesso! Uma senha temporária foi enviada para o seu email. Por favor, verifique a sua caixa de entrada (e spam).")
                                st.info("Você será redirecionado para a tela de login em breve...")
                                time.sleep(5)
                                # Volta para o login definindo o estado e recarregando
                                st.session_state['show_reset_view'] = False
                                st.rerun()
                            else:
                                st.error(
                                    "Ocorreu um erro ao enviar o email. Tente novamente mais tarde ou contacte o administrador.")
                        else:
                            st.error(senha_ou_erro)
                    else:
                        st.success(
                            "Se o email fornecido estiver associado a uma conta, uma senha temporária foi enviada.")
                        st.info("Verifique a sua caixa de entrada (e spam).")

    st.divider()
    # --- BOTÃO VOLTAR CORRIGIDO ---
    if st.button("⬅️ Voltar para o Login"):
        # Define o estado para False, indicando que não queremos mais ver a view de reset
        st.session_state['show_reset_view'] = False
        st.rerun()  # Recarrega a aplicação, o app.py mostrará o login_form

