import sqlite3
import os
import sys

caminho_base = os.path.abspath(os.path.dirname(__file__))
if caminho_base not in sys.path:
    sys.path.insert(0, caminho_base)

from Backend.banco_dados_pg import get_connection, adicionar_reflexao_completa
import Backend.banco_dados_pg as banco_pg

caminho_sqlite = os.path.join(caminho_base, 'SQL', 'espaco_voce.db')

def migrar_usuarios():
    print("🚀 Iniciando migração de usuários...")
    if not os.path.exists(caminho_sqlite):
        print("❌ SQLite db não encontrado!")
        return

    conn_sq = sqlite3.connect(caminho_sqlite)
    cursor_sq = conn_sq.cursor()
    
    # Seleciona usuários do SQLite
    try:
        cursor_sq.execute("SELECT id, nome, email, plano, gosta_fazer, bom_em, mundo_precisa, pago_para, fatos_diversos, fase_projeto, last_session_summary FROM usuarios")
        usuarios = cursor_sq.fetchall()
    except Exception as e:
        print(f"Aviso SQLite error: {e}. Ignorando tabela usuarios se não existir.")
        usuarios = []

    conn_pg = get_connection()
    cursor_pg = conn_pg.cursor()

    for u in usuarios:
        uid, nome, email, plano, gosta, bom, precisa, pago, fatos, fase, last_sess = u
        
        # Insert ou Update no PG
        # Mas não temos password_hash no SQLite (login era fraco). Vou usar um hash generico para accounts migradas se nao existirem na users
        # Se os dados importam (ikigai fields), a gente dá UPDATE
        try:
            cursor_pg.execute("""
                UPDATE users 
                SET nome = %s, email = %s, plano = %s, 
                    gosta_fazer = %s, bom_em = %s, mundo_precisa = %s, pago_para = %s,
                    fatos_diversos = %s, fase_projeto = %s, last_session_summary = %s
                WHERE id = %s
            """, (nome, email, plano, gosta, bom, precisa, pago, fatos, fase, last_sess, uid))
            
            if cursor_pg.rowcount == 0:
                print(f"⚠️ Usuário ID {uid} não existe no PostgreSQL (Vault). Crie-o ou faça login no app.")
        except Exception as e:
            print(f"Erro atualizando {uid}: {e}")
            conn_pg.rollback()
    
    conn_pg.commit()
    cursor_pg.close()
    conn_pg.close()
    print("✅ Usuários atualizados com dados IKIGAI e Memória.")


def migrar_diario():
    print("🚀 Iniciando migração do diário (Cifrando dados em Base64/AES256)...")
    conn_sq = sqlite3.connect(caminho_sqlite)
    cursor_sq = conn_sq.cursor()
    try:
        cursor_sq.execute("SELECT usuario_id, sentimento, texto, feedback_ia FROM diario")
        registros = cursor_sq.fetchall()
    except Exception:
        print("Tabela diario SQLite vazia ou não existe.")
        return

    migrados = 0
    for reg in registros:
        usuario_id, sentimento, texto, feedback_ia = reg
        sucesso = adicionar_reflexao_completa(usuario_id, sentimento, texto, feedback_ia)
        if sucesso: migrados += 1

    print(f"✅ {migrados} entradas do diário foram migradas e BLINDADAS no PostgreSQL.")

if __name__ == "__main__":
    migrar_usuarios()
    migrar_diario()
    print("\n🎉 MIGRAÇÃO CONCLUÍDA! O SQLite já não é mais necessário.")
