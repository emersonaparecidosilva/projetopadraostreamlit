# --------------------------------------------------------------------------------
# __init__.py (Ponto de Entrada do Pacote 'database')
#
# Descrição:
# Versão atualizada para incluir o novo submódulo de configurações (settings).
# --------------------------------------------------------------------------------

import streamlit as st
import mysql.connector

# Importa as funções dos submódulos para expô-las no nível do pacote
from .users import (
    hash_password, check_password, generate_strong_password, add_user, check_login,
    create_default_admin_if_needed, get_all_users, update_user_status,
    update_user_password, reset_user_password,find_user_by_email,update_user
)
from .printers import get_all_printers, add_printer, update_printer, update_printer_status, update_printer_details
from .sectors import get_all_sectors, add_sector, update_sector, update_sector_status
from .permissions import (
    check_page_access, get_all_page_permissions, update_page_permission,
    populate_initial_permissions
)
from .logs import log_action, get_all_logs
# --- 1. IMPORTA AS NOVAS FUNÇÕES DE SETTINGS ---
from .settings import get_setting, get_all_settings, set_setting, populate_initial_settings, set_multiple_settings

# --- Lógica de Criação de Tabelas (Centralizada) ---

def _create_all_tables(cursor):
    """Função interna para criar todas as tabelas do sistema."""
    # (As criações das tabelas users, printers, logs, sectors, permissions permanecem as mesmas)
    # ...
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, phone VARCHAR(20), email VARCHAR(255) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL, permission_level ENUM('admin', 'padrão', 'técnico') NOT NULL, status ENUM('ativo', 'inativo') NOT NULL DEFAULT 'ativo',force_password_change int)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS printers (id INT AUTO_INCREMENT PRIMARY KEY, unidade VARCHAR(255), fabricante VARCHAR(255), modelo VARCHAR(255), localizacao VARCHAR(255), setor VARCHAR(255), patrimonio VARCHAR(255) UNIQUE, nome VARCHAR(255), host VARCHAR(255), endereco_ip VARCHAR(45), status ENUM('Online', 'Offline', 'Desconhecido') NOT NULL DEFAULT 'Desconhecido', status_detalhado VARCHAR(255) DEFAULT 'Não verificado', toner_preto INT DEFAULT -1, toner_ciano INT DEFAULT -1, toner_magenta INT DEFAULT -1, toner_amarelo INT DEFAULT -1, contagem_paginas INT DEFAULT -1, ultima_verificacao TIMESTAMP NULL)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_logs (id INT AUTO_INCREMENT PRIMARY KEY, log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, performing_user_id INT, action_type VARCHAR(50) NOT NULL, details TEXT, FOREIGN KEY (performing_user_id) REFERENCES users(id) ON DELETE SET NULL)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sectors (id INT AUTO_INCREMENT PRIMARY KEY, location_tower VARCHAR(100) NOT NULL, location_floor VARCHAR(100) NOT NULL, sector_name VARCHAR(255) NOT NULL UNIQUE, cost_center VARCHAR(100), manager_name VARCHAR(255), manager_contact VARCHAR(255), status ENUM('ativo', 'inativo') NOT NULL DEFAULT 'ativo')
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS page_permissions (id INT AUTO_INCREMENT PRIMARY KEY, page_name VARCHAR(100) NOT NULL, permission_level ENUM('admin', 'padrão', 'técnico') NOT NULL, can_access BOOLEAN NOT NULL DEFAULT FALSE, UNIQUE KEY (page_name, permission_level))
    """)

    # --- 2. ADICIONA A CRIAÇÃO DA NOVA TABELA DE CONFIGURAÇÕES ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            setting_key VARCHAR(100) PRIMARY KEY,
            setting_value mediumtext
        )
    """)

# --- Função de Inicialização Principal ---

@st.cache_resource
def init_connection():
    """Inicializa a conexão e garante que toda a estrutura do banco de dados exista."""
    try:
        db_config = st.secrets["mysql"]
        conn = mysql.connector.connect(host=db_config["host"], user=db_config["user"], password=db_config["password"])
        cursor = conn.cursor()
        
        db_name = db_config["database"]
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.database = db_name

        _create_all_tables(cursor)
        conn.commit()
        cursor.close()
        
        # --- 3. ADICIONA A CHAMADA PARA POPULAR AS CONFIGURAÇÕES PADRÃO ---
        create_default_admin_if_needed(conn)
        populate_initial_permissions(conn)
        populate_initial_settings(conn) # <-- NOVO

        return conn
    except mysql.connector.Error as err:
        st.error(f"Erro crítico ao conectar ou configurar o MySQL: {err}")
        return None
    except KeyError:
        st.error("Configuração do banco de dados não encontrada em .streamlit/secrets.toml")
        return None

