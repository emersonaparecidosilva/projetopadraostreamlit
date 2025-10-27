# --------------------------------------------------------------------------------
# gerenciamento.py (Módulo da Página de Gerenciamento de Usuários)
#
# Autor: Emerson A. Silva
# Data: 22/10/2025
#
# Descrição:
# Versão consolidada que inclui o formulário para Adicionar novos utilizadores
# (com envio de email) e a funcionalidade de exportar a lista para CSV.
# --------------------------------------------------------------------------------

import streamlit as st
import database as db
import re
from utils.email_utils import enviar_email_senha

def show_gerenciamento_page(conn):
    """Renderiza a página de gerenciamento de usuários."""

    user_info = st.session_state.get("user_info", {})
    if user_info.get("permission_level") != "admin":
        st.error("Você não tem permissão para aceder a esta página.")
        st.stop()

    st.header("Gerenciamento de Usuários")
    admin_id = user_info.get("id")

    # Exibe a senha temporária se ela existir na sessão (do reset)
    if 'temp_password_info' in st.session_state:
        user_name = st.session_state.temp_password_info['name']
        temp_pass = st.session_state.temp_password_info['password']
        st.success(f"Senha temporária para **{user_name}**: `{temp_pass}`")
        st.warning("Anote a senha e a entregue ao Usuário. Ela não será exibida novamente.", icon="⚠️")
        del st.session_state['temp_password_info']

    # --- 1. FORMULÁRIO DE CADASTRO DE NOVO Usuário ---

    with st.expander("➕ Adicionar Usuário"):
        st.info("Uma senha temporária forte será gerada automaticamente e enviada para o email do novo Usuário.",
                icon="🔒")
        with st.form("signup_form_in_management", clear_on_submit=True):
            st.subheader("Informações do Novo Usuário")

            nome = st.text_input("Nome Completo *")
            telefone = st.text_input("Telefone (opcional)", placeholder="(XX) XXXXX-XXXX")
            email = st.text_input("Email *").lower()
            nivel_permissao = st.selectbox("Nível de Permissão *", ["padrão", "admin", "técnico"])

            submitted = st.form_submit_button("Cadastrar e Enviar Email")

            if submitted:
                email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                phone_regex = r'^\(?\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}$'

                if not (nome and email):
                    st.warning("Por favor, preencha todos os campos com *.")
                elif not re.match(email_regex, email):
                    st.error("Por favor, insira um endereço de email válido.")
                elif telefone and not re.match(phone_regex, telefone):
                    st.error("Formato de telefone inválido. Use o formato (XX) XXXXX-XXXX.")
                else:
                    try:
                        with st.spinner("A criar Usuário e a gerar senha..."):
                            success_db, senha_temp, message_db = db.add_user(conn, nome, telefone, email,
                                                                             nivel_permissao, admin_id)

                        if success_db:
                            st.write(message_db)  # "Usuário criado com sucesso!"

                            assunto_boas_vindas = "Bem-vindo ao Sistema de Gestão!"
                            corpo_boas_vindas = f"""
Olá {nome.split()[0]},

A sua conta foi criada no nosso Sistema de Gestão de Impressoras.

Para aceder, utilize a sua senha temporária abaixo:
Senha: {senha_temp}

Por motivos de segurança, ser-lhe-á pedido que altere esta senha no seu primeiro login.

Atenciosamente,
A Administração
"""
                            with st.spinner(f"A enviar email de boas-vindas para {email}..."):
                                email_sent = enviar_email_senha(
                                    email_destinatario=email,
                                    senha_temporaria=senha_temp,
                                    assunto=assunto_boas_vindas,
                                    corpo_template=corpo_boas_vindas
                                )

                            if email_sent:
                                st.success(f"Email enviado com sucesso para {email}!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(
                                    f"O Usuário foi criado, mas falhou o envio do email para {email}. Por favor, redefina a senha manualmente.")
                        else:
                            st.error(message_db)  # Ex: "Email já cadastrado"

                    except KeyError:
                        st.error(
                            "Erro de sessão. Não foi possível identificar o autor da ação. Faça o login novamente.")
                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado: {e}")

    st.divider()

    # --- 2. BUSCA E EXPORTAÇÃO DE UTILIZADORES ---
    st.subheader("Usuários Cadastrados")

    users_df = db.get_all_users(conn)

    col_search, col_export = st.columns([4, 1])
    with col_search:
        search_term = st.text_input("Buscar Usuário (por nome, email ou telefone):", key="search_user_manag")

    if search_term:
        mask = users_df.apply(lambda row:
                              search_term.lower() in str(row.get('name', '')).lower() or
                              search_term.lower() in str(row.get('email', '')).lower() or
                              search_term.lower() in str(row.get('phone', '')).lower(),
                              axis=1
                              )
        filtered_df = users_df[mask]
    else:
        filtered_df = users_df

    with col_export:
        if not filtered_df.empty:
            st.write("")  # Espaçamento
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar para CSV",
                data=csv,
                file_name='lista_utilizadores.csv',
                mime='text/csv',
                use_container_width=True
            )

    st.divider()

    # --- 3. LISTA E EDIÇÃO DE UTILIZADORES ---
    if filtered_df.empty:
        st.warning("Nenhum usuário encontrado.")
    else:
        for index, user in filtered_df.iterrows():
            user_id_int = int(user['id'])

            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 3, 3])
                with col1:
                    st.subheader(user['name'])
                    st.caption(f"Email: {user['email']} | Tel: {user.get('phone', 'N/A')}")
                with col2:
                    st.text(f"Permissão: {user['permission_level'].capitalize()}")
                    status_color = "🟢" if user['status'] == 'ativo' else "🔴"
                    st.text(f"Status: {status_color} {user['status'].capitalize()}")

                with col3:
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    with btn_col1:
                        if st.button("✏️ Editar", key=f"edit_{user_id_int}", use_container_width=True):
                            st.session_state['edit_user_id'] = user_id_int
                            st.rerun()
                    with btn_col2:
                        disabled_reset = (user_id_int == admin_id)
                        if st.button("🔑 Resetar", key=f"reset_{user_id_int}", disabled=disabled_reset,
                                     use_container_width=True, help="Gera uma nova senha aleatória para o usuário"):
                            success, new_password_or_error = db.reset_user_password(conn, user['email'], admin_id)
                            if success:
                                st.session_state['temp_password_info'] = {'name': user['name'],
                                                                          'password': new_password_or_error}
                                st.rerun()
                            else:
                                st.error(new_password_or_error)
                    with btn_col3:
                        new_status = 'inativo' if user['status'] == 'ativo' else 'ativo'
                        button_text = "🔴 Inativar" if user['status'] == 'ativo' else "🟢 Ativar"
                        disabled_status = (user_id_int == admin_id)
                        if st.button(button_text, key=f"status_{user_id_int}", disabled=disabled_status,
                                     use_container_width=True):
                            success, message = db.update_user_status(conn, user_id_int, new_status, admin_id)
                            if success:
                                st.toast(message, icon="✔️")
                                st.rerun()
                            else:
                                st.error(message)

            if st.session_state.get('edit_user_id') == user_id_int:
                with st.expander("Editando " + user['name'], expanded=True):
                    with st.form(key=f"form_edit_{user_id_int}"):
                        new_name = st.text_input("Nome", value=user['name'])
                        new_phone = st.text_input("Telefone", value=user.get('phone', ''))
                        new_email = st.text_input("Email", value=user['email'])
                        permission_options = ["padrão", "técnico", "admin"]
                        current_permission_index = 0
                        try:
                            current_permission_index = permission_options.index(user['permission_level'])
                        except ValueError:
                            pass
                        new_permission = st.selectbox("Nível de Permissão", options=permission_options,
                                                      index=current_permission_index)
                        col_save, col_cancel = st.columns(2)
                        if col_save.form_submit_button("Salvar Alterações", use_container_width=True):
                            success, message = db.update_user(conn, user_id_int, new_name, new_phone, new_email,
                                                              new_permission, admin_id)
                            if success:
                                st.success(message)
                                del st.session_state['edit_user_id']
                                st.rerun()
                            else:
                                st.error(message)
                        if col_cancel.form_submit_button("Cancelar", type="secondary", use_container_width=True):
                            del st.session_state['edit_user_id']
                            st.rerun()

