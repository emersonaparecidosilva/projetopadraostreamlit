import streamlit as st
import pandas as pd
import mysql.connector
from .logs import log_action

def populate_initial_permissions(conn):
    """Preenche a tabela de permissões com as regras padrão na primeira execução."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM page_permissions")
    # Verificamos apenas se a tabela está vazia. Se precisarmos adicionar novas regras,
    # a abordagem mais segura é limpar a tabela e deixar esta função recriá-las.
    cursor.execute("SELECT COUNT(*) FROM page_permissions")
    count = cursor.fetchone()[0]

    # Se a contagem for zero, popula tudo.
    # Se for maior que zero, mas não tiver a nova página, o admin precisa limpar a tabela.
    if count > 0:
        cursor.execute("SELECT COUNT(*) FROM page_permissions WHERE page_name = 'page_personalizacao'")
        if cursor.fetchone()[0] > 0:
            cursor.close()
            return # A tabela já está completa

    # --- LISTA DE PÁGINAS ATUALIZADA ---
    pages = [
        "page_home", "page_perfil", "page_ativos", "page_impressoras", "page_setores",
        "page_gerenciamento", "page_permissoes", "page_logs",
        "page_personalizacao"
    ]
    levels = ["admin", "técnico", "padrão"]

    # --- REGRAS DE ACESSO ATUALIZADAS ---
    default_rules = {
        "page_home": ["admin", "técnico", "padrão"],
        "page_perfil": ["admin", "técnico", "padrão"],
        "page_ativos": ["admin"],
        "page_impressoras": ["admin", "técnico"],
        "page_setores": ["admin"],
        "page_gerenciamento": ["admin"],
        "page_permissoes": ["admin"],
        "page_logs": ["admin"],
        "page_personalizacao": ["admin"]

    }
    
    rules_to_insert = []
    for page in pages:
        for level in levels:
            can_access = (level in default_rules.get(page, []))
            rules_to_insert.append((page, level, can_access))
    
    # Usa INSERT IGNORE para não dar erro se a regra já existir
    cursor.executemany(
        "INSERT IGNORE INTO page_permissions (page_name, permission_level, can_access) VALUES (%s, %s, %s)",
        rules_to_insert
    )
    conn.commit()
    cursor.close()

@st.cache_data(ttl=60)
def check_page_access(_conn, page_name, permission_level):
    if not permission_level: return False
    try:
        cursor = _conn.cursor(dictionary=True)
        cursor.execute("SELECT can_access FROM page_permissions WHERE page_name = %s AND permission_level = %s", (page_name, permission_level))
        result = cursor.fetchone()
        cursor.close()
        return result['can_access'] if result else False
    except mysql.connector.Error as err:
        print(f"Erro ao checar permissão de página: {err}")
        return False

def get_all_page_permissions(conn):
    try:
        return pd.read_sql("SELECT page_name, permission_level, can_access FROM page_permissions ORDER BY page_name, permission_level", conn)
    except mysql.connector.Error as err:
        print(f"Erro ao buscar permissões: {err}")
        return pd.DataFrame()

def update_page_permission(conn, page_name, permission_level, can_access, performing_user_id):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE page_permissions SET can_access = %s WHERE page_name = %s AND permission_level = %s", (can_access, page_name, permission_level))
        conn.commit()
        cursor.close()
        access_str = "CONCEDIDO" if can_access else "REMOVIDO"
        details = f"Admin (ID: {performing_user_id}) alterou o acesso do nível '{permission_level}' à página '{page_name}' para '{access_str}'."
        log_action(conn, performing_user_id, 'PERMISSION_CHANGED', details)
        check_page_access.clear()
        return True, "Permissão atualizada com sucesso!"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro ao atualizar permissão: {err}"
