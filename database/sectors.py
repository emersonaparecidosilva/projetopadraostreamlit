import pandas as pd
import mysql.connector
from .logs import log_action

def get_all_sectors(conn, only_active=False):
    try:
        query = "SELECT * FROM sectors"
        if only_active:
            query += " WHERE status = 'ativo'"
        query += " ORDER BY sector_name ASC"
        return pd.read_sql(query, conn)
    except mysql.connector.Error as err:
        print(f"Erro ao buscar setores: {err}")
        return pd.DataFrame()

def add_sector(conn, data, performing_user_id):
    try:
        cursor = conn.cursor()
        query = "INSERT INTO sectors (location_tower, location_floor, sector_name, cost_center, manager_name, manager_contact) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (data['location_tower'], data['location_floor'], data['sector_name'],
                  data['cost_center'], data['manager_name'], data['manager_contact'])
        cursor.execute(query, values)
        new_sector_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        details = f"Usuário (ID: {performing_user_id}) criou o setor '{data['sector_name']}' (ID: {new_sector_id})."
        log_action(conn, performing_user_id, 'SECTOR_CREATED', details)
        return True, "Setor adicionado com sucesso!"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro ao adicionar setor: {err}"

def update_sector(conn, sector_id, data, performing_user_id):
    try:
        cursor = conn.cursor()
        query = "UPDATE sectors SET location_tower = %s, location_floor = %s, sector_name = %s, cost_center = %s, manager_name = %s, manager_contact = %s WHERE id = %s"
        values = (data['location_tower'], data['location_floor'], data['sector_name'],
                  data['cost_center'], data['manager_name'], data['manager_contact'], sector_id)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        details = f"Usuário (ID: {performing_user_id}) atualizou o setor '{data['sector_name']}' (ID: {sector_id})."
        log_action(conn, performing_user_id, 'SECTOR_UPDATED', details)
        return True, "Setor atualizado com sucesso!"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro ao atualizar setor: {err}"

def update_sector_status(conn, sector_id, sector_name, new_status, performing_user_id):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE sectors SET status = %s WHERE id = %s", (new_status, sector_id))
        conn.commit()
        cursor.close()
        details = f"Usuário (ID: {performing_user_id}) alterou o status do setor '{sector_name}' (ID: {sector_id}) para '{new_status}'."
        log_action(conn, performing_user_id, 'SECTOR_STATUS_CHANGED', details)
        return True, "Status do setor alterado com sucesso!"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro ao alterar status do setor: {err}"
