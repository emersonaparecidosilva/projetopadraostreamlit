# --------------------------------------------------------------------------------
# printers.py (Módulo de Funções de Impressoras)
#
# Descrição:
# Contém todas as funções CRUD para a tabela 'printers', incluindo
# a nova função para atualizar os detalhes de monitoramento via SNMP.
# --------------------------------------------------------------------------------

import pandas as pd
import mysql.connector
from .logs import log_action

def get_all_printers(conn):
    """Busca todas as impressoras cadastradas e retorna como DataFrame."""
    try:
        return pd.read_sql("SELECT * FROM printers", conn)
    except mysql.connector.Error as err:
        print(f"Erro ao buscar impressoras: {err}")
        return pd.DataFrame()

def add_printer(conn, data, performing_user_id):
    """Adiciona uma nova impressora e registra a ação no log."""
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO printers (unidade, fabricante, modelo, localizacao, setor, patrimonio, nome, host, endereco_ip)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (data['unidade'], data['fabricante'], data['modelo'], data['localizacao'],
                  data['setor'], data['patrimonio'], data['nome'], data['host'], data['endereco_ip'])
        cursor.execute(query, values)
        new_printer_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        
        details = f"Usuário (ID: {performing_user_id}) adicionou a impressora '{data['nome']}' (ID: {new_printer_id})."
        log_action(conn, performing_user_id, 'PRINTER_CREATED', details)
        
        return True, "Impressora adicionada com sucesso!"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro ao adicionar impressora: {err}"

def update_printer(conn, printer_id, data, performing_user_id):
    """Atualiza dados de uma impressora e registra a ação no log."""
    try:
        cursor = conn.cursor()
        query = """
        UPDATE printers SET unidade = %s, fabricante = %s, modelo = %s, localizacao = %s, 
        setor = %s, patrimonio = %s, nome = %s, host = %s, endereco_ip = %s WHERE id = %s
        """
        values = (data['unidade'], data['fabricante'], data['modelo'], data['localizacao'],
                  data['setor'], data['patrimonio'], data['nome'], data['host'],
                  data['endereco_ip'], printer_id)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        
        details = f"Usuário (ID: {performing_user_id}) atualizou a impressora '{data['nome']}' (ID: {printer_id})."
        log_action(conn, performing_user_id, 'PRINTER_UPDATED', details)

        return True, "Impressora atualizada com sucesso!"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro ao atualizar impressora: {err}"

def update_printer_status(conn, printer_id, new_status):
    """Atualiza apenas o status 'Online'/'Offline' de uma impressora."""
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE printers SET status = %s WHERE id = %s", (new_status, printer_id))
        conn.commit()
        cursor.close()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Erro ao atualizar status da impressora {printer_id}: {err}")
        return False

# --- NOVA FUNÇÃO PARA SALVAR DADOS SNMP ---
def update_printer_details(conn, data):
    """
    Atualiza todos os dados de monitoramento de uma impressora no banco de dados.
    Esta função é chamada pelo processo de verificação automática via SNMP.
    """
    try:
        cursor = conn.cursor()
        query = """
            UPDATE printers SET
                status = %s,
                status_detalhado = %s,
                toner_preto = %s,
                toner_ciano = %s,
                toner_magenta = %s,
                toner_amarelo = %s,
                contagem_paginas = %s,
                ultima_verificacao = %s
            WHERE id = %s
        """
        values = (
            data.get('status', 'Desconhecido'),
            data.get('status_detalhado'),
            data.get('toner_preto', -1),
            data.get('toner_ciano', -1),
            data.get('toner_magenta', -1),
            data.get('toner_amarelo', -1),
            data.get('contagem_paginas', -1),
            data.get('ultima_verificacao'),
            data.get('id')
        )
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Erro ao atualizar detalhes da impressora ID {data.get('id')}: {err}")
        return False

