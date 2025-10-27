# --------------------------------------------------------------------------------
# logs.py (Módulo de Funções de Log)
#
# Descrição:
# Contém as funções para registrar e buscar registros da trilha de auditoria.
# --------------------------------------------------------------------------------

import mysql.connector
import pandas as pd

def log_action(conn, performing_user_id, action_type, details):
    """Registra uma ação na tabela de logs."""
    try:
        cursor = conn.cursor()
        query = "INSERT INTO user_logs (performing_user_id, action_type, details) VALUES (%s, %s, %s)"
        cursor.execute(query, (performing_user_id, action_type, details))
        conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print(f"ERRO DE LOG: {err}")
        conn.rollback()

# --- NOVA FUNÇÃO ---
def get_all_logs(conn):
    """
    Busca todos os registros de log, unindo com a tabela de usuários para
    obter o nome e email do autor da ação.
    """
    try:
        # A query usa LEFT JOIN para garantir que logs de usuários deletados ainda apareçam
        query = """
            SELECT
                l.log_timestamp AS 'Data e Hora',
                l.action_type AS 'Tipo de Ação',
                l.details AS 'Detalhes',
                u.name AS 'Nome do Usuário',
                u.email AS 'Email do Usuário'
            FROM
                user_logs l
            LEFT JOIN
                users u ON l.performing_user_id = u.id
            ORDER BY
                l.log_timestamp DESC
        """
        return pd.read_sql(query, conn)
    except mysql.connector.Error as err:
        print(f"Erro ao buscar logs: {err}")
        return pd.DataFrame()

