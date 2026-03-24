import os
import sys
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

# Importa a segurança que o usuário construiu em src/
caminho_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if caminho_base not in sys.path:
    sys.path.insert(0, caminho_base)

from src.security.encryption import security

def get_connection():
    """Retorna a conexão com o banco Docker usando psycopg2 configurado no .env"""
    db_host = os.getenv('DB_HOST', 'db')
    db_name = os.getenv('POSTGRES_DB', 'antigravity_db')
    db_user = os.getenv('POSTGRES_USER', 'antigravity_admin')
    db_pass = os.getenv('POSTGRES_PASSWORD')
    db_port = os.getenv('DB_PORT', '5432')
    
    try:
        return psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            port=db_port
        )
    except psycopg2.OperationalError as e:
        if db_host == 'db':
            # Fallback para testes rodando na máquina host (fora do Docker)
            return psycopg2.connect(
                host='localhost',
                database=db_name,
                user=db_user,
                password=db_pass,
                port=db_port
            )
        raise e

def criar_estruturas_iniciais():
    """Garante que as tabelas existam e ativa a extensão pgvector para RAG Semântico!"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Ativa o motor vetorial
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Tabela base de usuários
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                nome VARCHAR(100) DEFAULT 'Usuário',
                email VARCHAR(200),
                plano VARCHAR(50) DEFAULT 'free',
                gosta_fazer TEXT DEFAULT '',
                bom_em TEXT DEFAULT '',
                mundo_precisa TEXT DEFAULT '',
                pago_para TEXT DEFAULT '',
                fatos_diversos TEXT DEFAULT '',
                fase_projeto VARCHAR(50) DEFAULT 'Descoberta',
                last_session_summary TEXT DEFAULT ''
            );
        """)

        # Adicionar colunas faltantes se a tabela já existia sem elas
        colunas_para_adicionar = [
            ("nome", "VARCHAR(100) DEFAULT 'Usuário'"),
            ("email", "VARCHAR(200)"),
            ("plano", "VARCHAR(50) DEFAULT 'free'"),
            ("gosta_fazer", "TEXT DEFAULT ''"),
            ("bom_em", "TEXT DEFAULT ''"),
            ("mundo_precisa", "TEXT DEFAULT ''"),
            ("pago_para", "TEXT DEFAULT ''"),
            ("fatos_diversos", "TEXT DEFAULT ''"),
            ("fase_projeto", "VARCHAR(50) DEFAULT 'Descoberta'"),
            ("last_session_summary", "TEXT DEFAULT ''"),
        ]

        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users';")
        colunas_existentes = [row[0] for row in cur.fetchall()]

        for col, tipagem in colunas_para_adicionar:
            if col not in colunas_existentes:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {tipagem};")
                print(f"✅ Coluna '{col}' adicionada ao PostgreSQL table 'users'.")

        # Tabela do Diário Blindado + Vetor Matemático 🔒🧠
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sentimento VARCHAR(50),
                texto_encrypted BYTEA,
                feedback_ia_encrypted BYTEA,
                vetor_mensagem vector(384)
            );
        """)

        # Caso a tabela já exista do sqlite migrado, adicionamos a coluna
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='journal';")
        cols_journal = [row[0] for row in cur.fetchall()]
        if "vetor_mensagem" not in cols_journal:
            cur.execute("ALTER TABLE journal ADD COLUMN vetor_mensagem vector(384);")
            print("✅ Habilidade Semântica (vetor_mensagem) ativada na tabela journal.")

        # Tabela de Insights Simplificados
        cur.execute("""
            CREATE TABLE IF NOT EXISTS insights_diario (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                texto TEXT
            );
        """)

        # Tabela de Trilhas (Histórico de Sessões/Resumos de Fechamento)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trilhas (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resumo TEXT
            );
        """)

        # Tabela Mock para o usuário Teste (id=1) 
        # (Isso garante que o app não quebre se o usuário login "1" não existir no novo PG)
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cur.fetchone():
            from argon2 import PasswordHasher
            ph = PasswordHasher()
            hashe = ph.hash("senhaadmin123")
            cur.execute("""
                INSERT INTO users (id, username, password_hash, nome) 
                VALUES (1, 'admin', %s, 'Admin Master')
                ON CONFLICT (id) DO NOTHING
            """, (hashe,))
            # Sincroniza a sequencia do serial
            cur.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));")

        conn.commit()
    except Exception as e:
        print(f"⚠️ Erro ao inicializar estruturas no PG: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


# --- CRUD MÉTODOS ---

def buscar_trilhas(usuario_id, limite=5):
    """Busca o histórico de resumos (trilhas) formadas pelas sessões passadas."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT data, resumo FROM trilhas WHERE usuario_id = %s ORDER BY id DESC LIMIT %s", (usuario_id, limite))
        return cur.fetchall()
    except Exception as e:
        print(f"❌ Erro ao buscar trilhas: {e}")
        return []
    finally:
        conn.close()

def adicionar_trilha(usuario_id, resumo):
    """Adiciona um novo degrau na trilha do usuário (Summary de fim de sessão)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Salva o histórico acumulativo
        cur.execute("INSERT INTO trilhas (usuario_id, resumo) VALUES (%s, %s)", (usuario_id, resumo))
        
        # Opcional: Ainda atualiza last_session_summary para manter compatibilidade
        cur.execute("UPDATE users SET last_session_summary = %s WHERE id = %s", (resumo, usuario_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao salvar trilha: {e}")
        return False
    finally:
        conn.close()

def buscar_dados_usuario(usuario_id):
    """Retorna os dados base e Ikigai de um usuário."""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("""
            SELECT nome, email, plano, gosta_fazer, bom_em, mundo_precisa, pago_para 
            FROM users WHERE id = %s
        """, (usuario_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        print(f"❌ PG_Erro ao buscar perfil do usuário: {e}")
        return None
    finally:
        conn.close()


def atualizar_perfil_ikigai(usuario_id, nome, gosta, bom, precisa, pago):
    """Atualiza o perfil completo do usuário incluindo os 4 pilares do Ikigai."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users 
            SET nome = %s, gosta_fazer = %s, bom_em = %s, mundo_precisa = %s, pago_para = %s
            WHERE id = %s
        """, (nome, gosta, bom, precisa, pago, usuario_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ PG_Erro ao atualizar perfil Ikigai: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def visualizar_reflexoes_usuario(usuario_id, limite=5):
    """Busca as últimas entradas do diário para dar memória à IA, descriptografando no voo."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT data, sentimento, texto_encrypted, feedback_ia_encrypted 
            FROM journal 
            WHERE usuario_id = %s 
            ORDER BY id DESC LIMIT %s
        """, (usuario_id, limite))
        
        linhas = cur.fetchall()
        resultados_decifrados = []
        for data, sentimento, texto_encri, ia_encri in linhas:
            texto_puro = security.decrypt_data(bytes(texto_encri).decode())
            ia_puro = security.decrypt_data(bytes(ia_encri).decode()) if ia_encri else ""
            resultados_decifrados.append((data, sentimento, texto_puro, ia_puro))
        
        return resultados_decifrados
    except Exception as e:
        print(f"❌ PG_Erro ao buscar histórico: {e}")
        return []
    finally:
        conn.close()

def buscar_reflexoes_similares(usuario_id, vetor_pergunta, limite=3):
    """Busca as reflexões cujos vetores matemáticos sejam mais próximos da pergunta atual."""
    conn = get_connection()
    try:
        from pgvector.psycopg2 import register_vector
        register_vector(conn)
        
        cur = conn.cursor()
        query = """
            SELECT data, sentimento, texto_encrypted, feedback_ia_encrypted 
            FROM journal 
            WHERE usuario_id = %s AND vetor_mensagem IS NOT NULL
            ORDER BY vetor_mensagem <-> %s::vector 
            LIMIT %s
        """
        cur.execute(query, (usuario_id, vetor_pergunta, limite))
        
        linhas = cur.fetchall()
        resultados_decifrados = []
        for data, sentimento, texto_encri, ia_encri in linhas:
            texto_puro = security.decrypt_data(bytes(texto_encri).decode())
            ia_puro = security.decrypt_data(bytes(ia_encri).decode()) if ia_encri else ""
            resultados_decifrados.append((data, sentimento, texto_puro, ia_puro))
        
        return resultados_decifrados
    except Exception as e:
        print(f"❌ Erro na Busca Vetorial Semântica: {e}")
        return [] # Fallback
    finally:
        conn.close()


def adicionar_reflexao_completa(usuario_id, sentimento, texto, feedback_ia, vetor_matematico=None):
    """Envia texto pra IA, aplica AES-256 e guarda BLINDADO + VETORIZADO no Postgres."""
    conn = get_connection()
    try:
        from pgvector.psycopg2 import register_vector
        register_vector(conn)
        
        texto_encri = security.encrypt_data(texto).encode() # salva em bytes
        ia_encri = security.encrypt_data(feedback_ia).encode() if feedback_ia else None

        cur = conn.cursor()
        if vetor_matematico is not None:
            cur.execute("""
                INSERT INTO journal (usuario_id, sentimento, texto_encrypted, feedback_ia_encrypted, vetor_mensagem)
                VALUES (%s, %s, %s, %s, %s)
            """, (usuario_id, sentimento, texto_encri, ia_encri, vetor_matematico))
        else:
            cur.execute("""
                INSERT INTO journal (usuario_id, sentimento, texto_encrypted, feedback_ia_encrypted)
                VALUES (%s, %s, %s, %s)
            """, (usuario_id, sentimento, texto_encri, ia_encri))

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ PG_Erro ao salvar Reflexão Criptografada: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def buscar_insights_usuario(usuario_id, limite=5):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT data, texto FROM insights_diario WHERE usuario_id = %s ORDER BY id DESC LIMIT %s", (usuario_id, limite))
        return cur.fetchall()
    except Exception as e:
        print(f"❌ PG_Erro ao buscar insights: {e}")
        return []
    finally:
        conn.close()

def adicionar_insight(usuario_id, texto):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO insights_diario (usuario_id, texto) VALUES (%s, %s)", (usuario_id, texto))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ PG_Erro ao salvar insight: {e}")
        return False
    finally:
        conn.close()


def buscar_fase_projeto(usuario_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT fase_projeto FROM users WHERE id = %s", (usuario_id,))
        row = cur.fetchone()
        return row[0] if row and row[0] else "Descoberta"
    finally:
        conn.close()

def buscar_fatos_usuario(usuario_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT fatos_diversos FROM users WHERE id = %s", (usuario_id,))
        row = cur.fetchone()
        return row[0] if row and row[0] else ""
    finally:
        conn.close()

def atualizar_fatos_usuario(usuario_id, novos_fatos: str):
    conn = get_connection()
    try:
        existentes = buscar_fatos_usuario(usuario_id) or ""
        if novos_fatos.strip() in existentes: return True
        atualizado = (existentes + "\n" + novos_fatos).strip()
        
        cur = conn.cursor()
        cur.execute("UPDATE users SET fatos_diversos = %s WHERE id = %s", (atualizado, usuario_id))
        conn.commit()
        return True
    finally:
        conn.close()

def buscar_resumo_sessao(usuario_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT last_session_summary FROM users WHERE id = %s", (usuario_id,))
        row = cur.fetchone()
        return row[0] if row and row[0] else ""
    finally:
        conn.close()

def atualizar_resumo_sessao(usuario_id, resumo: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET last_session_summary = %s WHERE id = %s", (resumo, usuario_id))
        conn.commit()
        print(f"💾 PG_Resumo da Sessão atualizado para usuário {usuario_id}")
        return True
    finally:
        conn.close()

# Auto-Setup
criar_estruturas_iniciais()
