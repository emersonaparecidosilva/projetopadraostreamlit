# --------------------------------------------------------------------------------
# page_personalizacao.py (Módulo da Página de Personalização)
#
# Autor: Emerson A. Silva
# Data: 20/10/2025
#
# Descrição:
# Versão com upload de imagem para o fundo da tela de login,
# convertendo o arquivo para Base64 antes de salvar no banco.
# --------------------------------------------------------------------------------

import streamlit as st
import database as db
import base64 # Biblioteca para codificar a imagem

def show_personalizacao_page(conn):
    """Renderiza a página para personalizar a tela de login."""

    user_info = st.session_state.get("user_info", {})
    if user_info.get("permission_level") != "admin":
        st.error("Acesso negado. Apenas administradores podem acessar esta página.")
        st.stop()

    st.header("🎨 Personalizar Tela de Login")
    admin_id = user_info.get("id")

    # Busca as configurações atuais do banco, usando a nova chave 'login_bg_base64'
    current_settings = db.get_all_settings(conn)
    current_title = current_settings.get('login_title', 'Login do Sistema')
    current_bg_base64 = current_settings.get('login_bg_base64', '')

    with st.form("personalizacao_form"):
        st.subheader("Configurações de Aparência")
        
        new_title = st.text_input(
            "Título da Página de Login",
            value=current_title
        )
        
        st.divider()
        
        # Exibe uma prévia da imagem de fundo atual, se existir
        if current_bg_base64:
            st.write("Imagem de Fundo Atual:")
            st.image(current_bg_base64)
            # Oferece a opção de remover a imagem
            if st.checkbox("Remover imagem de fundo atual"):
                # Usamos um valor especial para marcar a imagem para remoção
                current_bg_base64 = "REMOVE" 
        
        # Campo para upload de uma nova imagem
        uploaded_file = st.file_uploader(
            "Anexar nova imagem de fundo (JPG, PNG)",
            type=['png', 'jpg', 'jpeg'],
            help="Deixe em branco para manter a imagem atual ou nenhuma."
        )

        submitted = st.form_submit_button("Salvar Alterações", use_container_width=True)
        if submitted:
            settings_to_save = {'login_title': new_title}
            
            # Lógica para decidir se a imagem deve ser atualizada, removida ou mantida
            if current_bg_base64 == "REMOVE":
                # Se o admin marcou a caixa, salva um valor vazio no banco
                settings_to_save['login_bg_base64'] = ""
            elif uploaded_file is not None:
                # Se um novo arquivo foi anexado, converte-o para Base64
                image_bytes = uploaded_file.getvalue()
                base64_string = base64.b64encode(image_bytes).decode()
                mime_type = uploaded_file.type
                # Monta a Data URI completa, que o navegador entende
                settings_to_save['login_bg_base64'] = f"data:{mime_type};base64,{base64_string}"
            
            # Se nenhuma ação foi tomada sobre a imagem, o dicionário conterá apenas
            # o 'login_title', e a imagem no banco não será alterada.
            
            # Chama a função que salva todas as alterações de uma vez
            success, message = db.set_multiple_settings(conn, settings_to_save, admin_id)

            if success:
                st.success(message)
                # Limpa os caches para que a mudança seja refletida em toda a aplicação
                db.get_all_settings.clear()
                db.get_setting.clear()
                st.rerun()
            else:
                st.error(message)

