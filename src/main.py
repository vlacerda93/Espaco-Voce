import os
import sys
import psycopg2
import getpass
from datetime import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Importa sua lógica de criptografia
sys.path.append('src')
from security.encryption import security

ph = PasswordHasher()

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

def fazer_login():
    print("\n🔐 --- ACESSO RESTRITO: ANTIGRAVITY ---")
    usuario = input("Usuário: ")
    senha = getpass.getpass("Senha Mestra: ")
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT password_hash FROM users WHERE username = %s', (usuario,))
        resultado = cur.fetchone()
    except Exception as e:
        print(f"Erro ao acessar banco: {e}")
        return False
    finally:
        cur.close()
        conn.close()

    if resultado:
        hash_banco = resultado[0]
        try:
            ph.verify(hash_banco, senha)
            print(f"\n✅ Acesso concedido! Bem-vindo, {usuario}.")
            return True
        except VerifyMismatchError:
            print("\n❌ Senha incorreta!")
            return False
    else:
        print("\n❌ Usuário não encontrado!")
        return False

# --- FUNÇÕES DO COFRE ---
def log_access(servico, sucesso, detalhes):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO access_logs (servico_consultado, status_sucesso, detalhes) VALUES (%s, %s, %s)',
                (servico, sucesso, detalhes))
    conn.commit()
    cur.close()
    conn.close()

def salvar_senha():
    servico = input("Nome do Serviço: ")
    usuario = input("Usuário: ")
    senha = input("Senha: ")
    senha_cripto = security.encrypt_data(senha)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO vault (servico, usuario, senha_criptografada) VALUES (%s, %s, %s)',
                (servico, usuario, senha_cripto))
    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✅ {servico} salvo!")

def buscar_senha():
    servico = input("Buscar qual serviço? ")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT usuario, senha_criptografada FROM vault WHERE servico ILIKE %s', (servico,))
    item = cur.fetchone()
    if item:
        usuario, senha_cripto = item
        senha_final = security.decrypt_data(senha_cripto)
        print(f"\n🔑 Usuário: {usuario} | Senha: {senha_final}")
        log_access(servico, True, "Acesso via menu.")
    else:
        print("\n❌ Não encontrado.")
        log_access(servico, False, "Busca falhou.")
    cur.close()
    conn.close()

def ver_logs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT 10;')
    print("\n--- ÚLTIMOS ACESSOS ---")
    for log in cur.fetchall():
        status = "✅" if log[3] else "❌"
        data_f = log[2].strftime('%d/%m %H:%M')
        print(f"{data_f} | {status} | {log[1]}")
    cur.close()
    conn.close()

# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    if fazer_login():
        while True:
            print("\n--- ANTIGRAVITY VAULT ---")
            print("1. Salvar | 2. Buscar | 3. Logs | 4. Sair")
            opcao = input("Escolha: ")
            if opcao == "1": salvar_senha()
            elif opcao == "2": buscar_senha()
            elif opcao == "3": ver_logs()
            elif opcao == "4": break
    else:
        print("Sistema encerrado.")
