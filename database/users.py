import bcrypt
import pandas as pd
import mysql.connector
import secrets
import string

# Importa funções de outros módulos do mesmo pacote
from .logs import log_action

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_strong_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password) and any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and any(c in "!@#$%^&*" for c in password)):
            return password


def add_user(conn, name, phone, email, permission_level, performing_user_id=None):
    """
    Adiciona um novo utilizador, gera uma senha temporária automaticamente
    e define a flag force_password_change como TRUE.
    Retorna (True, senha_em_texto_puro, mensagem_sucesso) em caso de sucesso.
    """
    try:
        # 1. Gera a senha temporária
        new_password = generate_strong_password()
        hashed_pw = hash_password(new_password)

        cursor = conn.cursor()

        # 2. Insere o utilizador com a senha e a flag
        query = """
                INSERT INTO users (name, phone, email, password, permission_level, force_password_change)
                VALUES (%s, %s, %s, %s, %s, TRUE) \
                """
        params = (name, phone, email, hashed_pw, permission_level)

        cursor.execute(query, params)
        new_user_id = cursor.lastrowid
        conn.commit()
        cursor.close()

        if performing_user_id:
            details = f"Utilizador (ID: {performing_user_id}) criou o novo utilizador '{email}' (ID: {new_user_id}). Senha temporária gerada."
            log_action(conn, performing_user_id, 'USER_CREATED', details)

        # 3. Retorna a senha em texto puro para ser enviada por email
        return True, new_password, "Utilizador criado com sucesso! Email com senha temporária será enviado."

    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062:  # Erro de entrada duplicada
            return False, None, "Erro: O email fornecido já está cadastrado."
        return False, None, f"Erro ao adicionar utilizador: {err}"

def check_login(conn, email, password):
    """Verifica credenciais e retorna dados do utilizador, incluindo force_password_change."""
    try:
        cursor = conn.cursor(dictionary=True)
        # Ainda seleciona a flag force_password_change
        cursor.execute("SELECT *, force_password_change FROM users WHERE email = %s AND status = 'ativo'", (email,))
        user = cursor.fetchone()
        cursor.close()
        if user and check_password(password, user['password']):
            details = f"Utilizador '{email}' (ID: {user['id']}) efetuou login."
            # Chama log_action sem IP e User-Agent
            log_action(conn, user['id'], 'USER_LOGIN', details)
            return user
        return None
    except mysql.connector.Error as err:
        print(f"Erro de banco de dados no login: {err}")
        return None


def create_default_admin_if_needed(conn):
    """Cria o utilizador admin padrão na primeira execução."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # 1. Gera uma senha forte para o admin padrão
        admin_password = generate_strong_password()
        hashed_pw = hash_password(admin_password)

        try:
            # 2. Insere o admin diretamente
            cursor.execute(
                "INSERT INTO users (name, phone, email, password, permission_level, force_password_change) VALUES (%s, %s, %s, %s, %s, %s)",
                ("Admin Padrão", "N/A", "admin@projeto.com", hashed_pw, "admin", True)
                # Força a troca da senha no primeiro login
            )
            conn.commit()

            # 3. Imprime a senha no terminal (APENAS na primeira execução)
            print("=" * 50)
            print("PRIMEIRA EXECUÇÃO: UTILIZADOR ADMIN CRIADO")
            print(f"Email: admin@projeto.com")
            print(f"Senha Temporária: {admin_password}")
            print("Por favor, guarde esta senha e altere-a no primeiro login.")
            print("=" * 50)

        except Exception as e:
            print(f"Erro ao criar admin padrão: {e}")
            conn.rollback()

    cursor.close()

def get_all_users(conn):
    return pd.read_sql("SELECT id, name, phone, email, permission_level, status FROM users", conn)


# --- NOVA FUNÇÃO AUXILIAR ---
def find_user_by_email(conn, email):
    """Verifica se um utilizador existe com o email fornecido."""
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user_exists = cursor.fetchone()
        cursor.close()
        return user_exists is not None # Retorna True se encontrou, False caso contrário
    except mysql.connector.Error as err:
        print(f"Erro ao buscar utilizador por email: {err}")
        return False

def update_user_status(conn, user_id, new_status, performing_user_id):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = %s WHERE id = %s", (new_status, user_id))
        conn.commit()
        cursor.close()
        details = f"Usuário (ID: {performing_user_id}) alterou o status do usuário (ID: {user_id}) para '{new_status}'."
        log_action(conn, performing_user_id, 'USER_STATUS_CHANGED', details)
        return True, "Status alterado com sucesso!"
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro ao atualizar status: {err}"


def update_user_password(conn, user_id, old_password, new_password, performing_user_id):
    """Altera a senha do utilizador e desativa a flag 'force_password_change'."""
    try:
        cursor = conn.cursor(dictionary=True)
        # Busca a senha atual para verificação
        cursor.execute("SELECT password, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        # Verifica se o utilizador existe e se a senha antiga está correta
        if user and check_password(old_password, user['password']):
            new_hashed_pw = hash_password(new_password)

            # --- PONTO CRÍTICO DA CORREÇÃO ---
            # Garante que a query UPDATE define force_password_change = FALSE
            update_query = "UPDATE users SET password = %s, force_password_change = FALSE WHERE id = %s"
            cursor.execute(update_query, (new_hashed_pw, user_id))
            # --- FIM DA CORREÇÃO ---

            conn.commit()
            cursor.close()

            # Regista o log da alteração
            details = f"Utilizador (ID: {performing_user_id}) alterou a própria senha."
            log_action(conn, performing_user_id, 'PASSWORD_CHANGED', details)

            return True, "Senha alterada com sucesso!"
        else:
            # Se a senha antiga estiver incorreta ou o utilizador não for encontrado
            cursor.close()
            return False, "Senha antiga incorreta."

    except mysql.connector.Error as err:
        conn.rollback()  # Desfaz a operação em caso de erro
        return False, f"Erro de banco de dados ao alterar senha: {err}"


def reset_user_password(conn, user_email, performing_user_id):
    """
    Gera nova senha, atualiza no banco, ativa a flag 'force_password_change'
    e retorna a senha temporária em texto puro.
    """
    try:
        # Busca o ID do utilizador pelo email
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            return False, "Utilizador não encontrado com este email."

        user_id_to_reset = user['id']

        # Gera a nova senha e o hash
        new_password = generate_strong_password()
        new_hashed_pw = hash_password(new_password)

        # Atualiza a senha E ativa a flag force_password_change
        cursor.execute("UPDATE users SET password = %s, force_password_change = TRUE WHERE id = %s",
                       (new_hashed_pw, user_id_to_reset))
        conn.commit()
        cursor.close()

        details = f"Admin (ID: {performing_user_id}) solicitou reset de senha para o utilizador '{user_email}' (ID: {user_id_to_reset})."
        log_action(conn, performing_user_id, 'PASSWORD_RESET_REQUESTED', details)  # Log da solicitação

        # Retorna sucesso e a senha em TEXTO PURO para envio por email
        return True, new_password

    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Erro de banco de dados ao resetar senha: {err}"

def update_user(conn, user_id, name, phone, email, permission_level, performing_user_id):
    """
    Atualiza os dados de um usuário (nome, telefone, email, nível de permissão)
    no banco de dados e registra a ação no log.
    """
    try:
        cursor = conn.cursor()
        
        # Query para atualizar os dados do usuário
        query = """
        UPDATE users 
        SET name = %s, phone = %s, email = %s, permission_level = %s 
        WHERE id = %s
        """
        params = (name, phone, email, permission_level, user_id)
        
        cursor.execute(query, params)
        conn.commit()
        
        rows_affected = cursor.rowcount
        cursor.close()
        
        if rows_affected > 0:
            # Registrar a ação no log
            details = (
                f"Usuário (ID: {performing_user_id}) atualizou dados do usuário (ID: {user_id}). "
                f"Novos dados: Nome='{name}', Telefone='{phone}', Email='{email}', Permissão='{permission_level}'."
            )
            log_action(conn, performing_user_id, 'USER_DATA_UPDATED', details)
            return True, "Dados do usuário atualizados com sucesso!"
        else:
            return False, "Nenhum usuário foi encontrado com o ID fornecido."

    except mysql.connector.Error as err:
        conn.rollback()
        # Verifica se o erro é de entrada duplicada (ex: email já existe)
        if err.errno == 1062:
            return False, "Erro: O email fornecido já está em uso por outro usuário."
        return False, f"Erro de banco de dados ao atualizar usuário: {err}"