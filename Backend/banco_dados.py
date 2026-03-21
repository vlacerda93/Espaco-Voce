import sqlite3
import os

# --- CONFIGURAÇÃO DE CAMINHO ---
# Garante que o Python encontre a pasta SQL independente de onde o script é rodado
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_banco = os.path.join(diretorio_atual, '..', 'SQL', 'espaco_voce.db')

def buscar_dados_usuario(usuario_id):
    """Busca Nome, Email e Plano do usuário para tornar o prompt da IA dinâmico."""
    try:
        conn = sqlite3.connect(caminho_banco)
        # Permite acessar os dados pelo nome da coluna (ex: linha['nome'])
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute("SELECT nome, email, plano FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = cursor.fetchone()
        conn.close()
        return usuario
    except Exception as e:
        print(f"❌ Erro ao buscar perfil do usuário: {e}")
        return None

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

if __name__ == "__main__":
    visualizador_reflexoes_terminal()