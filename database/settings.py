# --------------------------------------------------------------------------------
# settings.py (Módulo de Funções de Configurações do Sistema)
#
# Descrição:
# Versão com uma nova função para salvar múltiplas configurações de forma
# transacional, garantindo a integridade dos dados.
# --------------------------------------------------------------------------------

import streamlit as st
import mysql.connector
from .logs import log_action

@st.cache_data(ttl=60)
def get_setting(_conn, setting_key):
    """Busca o valor de uma configuração específica no banco de dados."""
    try:
        cursor = _conn.cursor(dictionary=True)
        cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = %s", (setting_key,))
        result = cursor.fetchone()
        cursor.close()
        return result['setting_value'] if result else None
    except mysql.connector.Error as err:
        print(f"Erro ao buscar configuração '{setting_key}': {err}")
        return None

@st.cache_data(ttl=60)
def get_all_settings(_conn):
    """Busca todas as configurações e retorna como um dicionário."""
    settings = {}
    try:
        cursor = _conn.cursor(dictionary=True)
        cursor.execute("SELECT setting_key, setting_value FROM system_settings")
        results = cursor.fetchall()
        cursor.close()
        for row in results:
            settings[row['setting_key']] = row['setting_value']
        return settings
    except mysql.connector.Error as err:
        print(f"Erro ao buscar todas as configurações: {err}")
        return settings

def set_setting(conn, setting_key, setting_value, performing_user_id):
    """Salva ou atualiza uma configuração no banco de dados e registra no log."""
    try:
        cursor = conn.cursor()
        query = "INSERT INTO system_settings (setting_key, setting_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)"
        cursor.execute(query, (setting_key, setting_value))
        conn.commit()
        cursor.close()

        details = f"Admin (ID: {performing_user_id}) atualizou a configuração '{setting_key}'."
        log_action(conn, performing_user_id, 'SETTING_UPDATED', details)
        return True, "Configuração salva com sucesso!"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro ao salvar configuração: {err}"

# --- NOVA FUNÇÃO ROBUSTA ---
def set_multiple_settings(conn, settings_dict, performing_user_id):
    """
    Salva ou atualiza múltiplas configurações em uma única transação segura.
    Se uma falhar, todas são desfeitas (rollback).
    """
    try:
        cursor = conn.cursor()
        query = "INSERT INTO system_settings (setting_key, setting_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)"
        
        # Prepara os dados para a inserção em lote
        data_to_save = list(settings_dict.items())
        cursor.executemany(query, data_to_save)

        # Registra um log para cada alteração individual
        for key, value in settings_dict.items():
            details = f"Admin (ID: {performing_user_id}) atualizou a configuração '{key}'."
            log_action(conn, performing_user_id, 'SETTING_UPDATED', details)

        conn.commit()
        cursor.close()
        return True, "Configurações salvas com sucesso!"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro ao salvar configurações: {err}"


def populate_initial_settings(conn):
    """Garante que as configurações padrão existam na primeira execução."""
    cursor = conn.cursor()
    # --- ALTERAÇÃO AQUI: Renomeia 'login_bg_url' para 'login_bg_base64' ---
    cursor.execute("""
        INSERT IGNORE INTO system_settings (setting_key, setting_value)
        VALUES ('login_title', 'Login do Sistema'), ('login_bg_base64', '')
    """)
    conn.commit()
    cursor.close()

