# --------------------------------------------------------------------------------
# email_utils.py (Módulo de Utilitários de Email)
#
# Autor: Emerson A. Silva
# Data: 22/10/2025
#
# Descrição:
# Função de envio de email refatorada para aceitar um assunto e corpo
# personalizáveis, mantendo a retrocompatibilidade.
# --------------------------------------------------------------------------------

import streamlit as st
import smtplib
import ssl
from email.message import EmailMessage


def enviar_email_senha(email_destinatario, senha_temporaria, assunto=None, corpo_template=None):
    """
    Envia um e-mail com uma senha, usando um modelo de corpo e assunto personalizável.
    Se o assunto ou o corpo não forem fornecidos, usa o padrão de "Redefinição de Senha".
    """
    try:
        # --- LÊ AS CREDENCIAIS DO SECRETS ---
        email_config = st.secrets["email"]
        email_sender = email_config["sender_email"]
        email_password = email_config["sender_password"]
        smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
        smtp_port = email_config.get("smtp_port", 465)

        # --- LÓGICA DE TEMPLATE ---
        if assunto is None:
            assunto = "Redefinição de Senha - Sistema de Gestão"

        if corpo_template is None:
            corpo_template = """
Olá,

Uma redefinição de senha foi solicitada para sua conta.
Sua nova senha temporária é: {senha}

Por favor, faça login utilizando esta senha e altere-a imediatamente
na página "Meu Perfil" por motivos de segurança.

Atenciosamente,
Sistema de Gestão de Impressoras
"""

        # Formata o corpo do email com a senha fornecida
        corpo = corpo_template.format(senha=senha_temporaria)

        # --- CRIA E ENVIA O EMAIL ---
        msg = EmailMessage()
        msg['Subject'] = assunto
        msg['From'] = email_sender
        msg['To'] = email_destinatario
        msg.set_content(corpo)

        contexto_ssl = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=contexto_ssl) as smtp:
            smtp.login(email_sender, email_password)
            smtp.send_message(msg)

        return True

    except KeyError:
        st.error("Configuração 'email' (sender_email, sender_password) não encontrada no st.secrets.")
        return False
    except smtplib.SMTPAuthenticationError:
        st.error("Erro de autenticação SMTP. Verifique o email e a senha do remetente no st.secrets.")
        return False
    except smtplib.SMTPException as e:
        st.error(f"Erro de SMTP ao enviar e-mail: {e}")
        return False
    except Exception as e:
        st.error(f"Erro inesperado ao enviar e-mail: {e}")
        return False

