import sqlite3
import os

# --- CONFIGURAÇÃO DE CAMINHO ---
# Garante que o Python encontre a pasta SQL independente de onde o script é rodado
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_banco = os.path.join(diretorio_atual, '..', 'SQL', 'espaco_voce.db')

def buscar_dados_usuario(usuario_id):
    """Busca Nome, Email, Plano e dados de Ikigai do usuário."""
    try:
        conn = sqlite3.connect(caminho_banco)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute("SELECT nome, email, plano, gosta_fazer, bom_em, mundo_precisa, pago_para FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = cursor.fetchone()
        conn.close()
        return usuario
    except Exception as e:
        print(f"❌ Erro ao buscar perfil do usuário: {e}")
        return None

def atualizar_perfil_ikigai(usuario_id, nome, gosta, bom, precisa, pago):
    """Atualiza o perfil completo do usuário incluindo os 4 pilares do Ikigai."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios 
            SET nome = ?, gosta_fazer = ?, bom_em = ?, mundo_precisa = ?, pago_para = ?
            WHERE id = ?
        """, (nome, gosta, bom, precisa, pago, usuario_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar perfil: {e}")
        return False

def visualizar_reflexoes_usuario(usuario_id, limite=3):
    """Busca as últimas entradas do diário para dar memória persistente à IA."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        # Selecionamos as colunas exatas que a IA precisa ler
        cursor.execute("""
            SELECT data, sentimento, texto, feedback_ia 
            FROM diario 
            WHERE usuario_id = ? 
            ORDER BY id DESC LIMIT ?
        """, (usuario_id, limite))
        dados = cursor.fetchall()
        conn.close()
        return dados
    except Exception as e:
        print(f"❌ Erro ao buscar histórico: {e}")
        return []

def adicionar_reflexao_completa(usuario_id, sentimento, texto, feedback_ia):
    """Salva a nova interação no banco usando a coluna 'texto'."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO diario (usuario_id, data, sentimento, texto, feedback_ia)
            VALUES (?, datetime('now', 'localtime'), ?, ?, ?)
        """, (usuario_id, sentimento, texto, feedback_ia))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")
        return False

def visualizador_reflexoes_terminal():
    """Interface visual simples para conferir os dados salvos no terminal."""
    if not os.path.exists(caminho_banco):
        print(f"❌ Banco não encontrado em: {caminho_banco}")
        return

    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        # JOIN une as tabelas para mostrar o nome do usuário ao lado da mensagem
        query = """
            SELECT u.nome, d.data, d.sentimento, d.texto, d.feedback_ia
            FROM diario d
            JOIN usuarios u ON d.usuario_id = u.id
            ORDER BY d.data DESC
        """
        cursor.execute(query)
        registros = cursor.fetchall()

        if not registros:
            print("\n📭 O diário ainda está vazio.")
        else:
            print("\n" + "="*80)
            print(f"{'RELATÓRIO DE INTERAÇÕES - ESPAÇO VOCÊ':^80}")
            print("="*80)
            for reg in registros:
                print(f"📅 DATA: {reg[1]} | 👤 USUÁRIO: {reg[0]} | 🎭 HUMOR: {reg[2]}")
                print(f"📝 ENTRADA: {reg[3]}")
                print(f"✨ INSIGHT IA: {reg[4]}")
                print("-" * 80)
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao gerar visualização: {e}")

def criar_tabela_insights():
    """Cria a tabela de insights se não existir."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insights_diario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                data DATETIME,
                texto TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao criar tabela de insights: {e}")

def adicionar_insight(usuario_id, texto):
    """Salva um novo insight no diário de insights."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO insights_diario (usuario_id, data, texto)
            VALUES (?, datetime('now', 'localtime'), ?)
        """, (usuario_id, texto))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar insight: {e}")
        return False

def buscar_insights_usuario(usuario_id, limite=5):
    """Busca os últimos insights salvos pelo usuário."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data, texto 
            FROM insights_diario 
            WHERE usuario_id = ? 
            ORDER BY id DESC LIMIT ?
        """, (usuario_id, limite))
        dados = cursor.fetchall()
        conn.close()
        return dados
    except Exception as e:
        print(f"❌ Erro ao buscar insights: {e}")
        return []

# --- MIGRAÇÃO: Colunas de Memória Dinâmica ---
def _migrar_colunas_usuario():
    """Adiciona colunas fatos_diversos e fase_projeto se não existirem."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        # Verifica colunas existentes
        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = [col[1] for col in cursor.fetchall()]
        if "fatos_diversos" not in colunas:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN fatos_diversos TEXT DEFAULT ''")
            print("✅ Coluna 'fatos_diversos' adicionada à tabela usuarios.")
        if "fase_projeto" not in colunas:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN fase_projeto TEXT DEFAULT 'Descoberta'")
            print("✅ Coluna 'fase_projeto' adicionada à tabela usuarios.")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Migração de colunas: {e}")


def buscar_fatos_usuario(usuario_id):
    """Retorna o texto livre de fatos diversos do usuário."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("SELECT fatos_diversos FROM usuarios WHERE id = ?", (usuario_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] else ""
    except Exception as e:
        print(f"❌ Erro ao buscar fatos: {e}")
        return ""


def atualizar_fatos_usuario(usuario_id, novos_fatos: str):
    """Acrescenta novos fatos ao campo existente, sem sobrescrever."""
    try:
        existentes = buscar_fatos_usuario(usuario_id)
        # Evita duplicatas triviais
        if novos_fatos.strip() in existentes:
            return True
        atualizado = (existentes + "\n" + novos_fatos).strip()
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET fatos_diversos = ? WHERE id = ?", (atualizado, usuario_id))
        conn.commit()
        conn.close()
        print(f"💾 Fatos atualizados para usuário {usuario_id}")
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar fatos: {e}")
        return False


def buscar_fase_projeto(usuario_id):
    """Retorna a fase atual do projeto do usuário."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("SELECT fase_projeto FROM usuarios WHERE id = ?", (usuario_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] else "Descoberta"
    except Exception as e:
        print(f"❌ Erro ao buscar fase: {e}")
        return "Descoberta"


def atualizar_fase_projeto(usuario_id, nova_fase: str):
    """Atualiza a fase do projeto (Descoberta, Planejamento, Execução, Revisão)."""
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET fase_projeto = ? WHERE id = ?", (nova_fase, usuario_id))
        conn.commit()
        conn.close()
        print(f"🔄 Fase do projeto atualizada para '{nova_fase}' (usuário {usuario_id})")
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar fase: {e}")
        return False


# Executa a criação da tabela e migração na importação
criar_tabela_insights()
_migrar_colunas_usuario()

if __name__ == "__main__":
    visualizador_reflexoes_terminal()