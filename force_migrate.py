import sqlite3
import os
import sys
from sentence_transformers import SentenceTransformer

# --- CONFIGURAÇÃO DE CAMINHO ---
caminho_base = os.path.abspath(os.path.dirname(__file__))
if caminho_base not in sys.path:
    sys.path.insert(0, caminho_base)

import Backend.banco_dados_pg as banco_pg

caminho_sqlite = os.path.join(caminho_base, 'SQL', 'espaco_voce.db')

def force_migration():
    print("🚀 Inicia Migração de Força Bruta (Cifrando + Vetorizando)...")
    
    # 1. Carrega o modelo de vetores
    modelo = SentenceTransformer('all-MiniLM-L6-v2')
    
    conn_sq = sqlite3.connect(caminho_sqlite)
    cursor_sq = conn_sq.cursor()
    
    # Pega tudo do diário SQLite
    cursor_sq.execute("SELECT id, usuario_id, sentimento, texto, feedback_ia, data FROM diario")
    rows = cursor_sq.fetchall()
    
    conn_pg = banco_pg.get_connection()
    cur_pg = conn_pg.cursor()
    
    # Verifica o que já tem no PG para não duplicar (mesmo texto e data)
    # Mas como o texto está criptografado no PG, vamos pelo ID original ou apenas limpamos por segurança?
    # Para simplificar e garantir 85 entradas, vamos limpar a journal do PG (id > 1) ou apenas ignorar erros.
    # Na verdade, vou deletar a journal do PG e repopular tudo do zero para ficar perfeito.
    print("🧹 Limpando journal atual do PostgreSQL para reinicio limpo...")
    cur_pg.execute("TRUNCATE TABLE journal RESTART IDENTITY CASCADE")
    conn_pg.commit()

    migrados = 0
    for r in rows:
        sid, uid, sent, texto, ia, data = r
        # UID no SQLITE é 1. No PG também temos o admin como 1.
        
        try:
            # Vetoriza o texto puro
            vetor = modelo.encode(texto).tolist()
            
            # Criptografa
            texto_encri = banco_pg.security.encrypt_data(texto).encode()
            ia_encri = banco_pg.security.encrypt_data(ia).encode() if ia else None
            
            cur_pg.execute("""
                INSERT INTO journal (usuario_id, sentimento, texto_encrypted, feedback_ia_encrypted, vetor_mensagem, data)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (1, sent, texto_encri, ia_encri, vetor, data))
            migrados += 1
            if migrados % 10 == 0: print(f"✅ Migrados {migrados}...")
        except Exception as e:
            print(f"❌ Erro no ID {sid}: {e}")
            
    conn_pg.commit()
    print(f"🎉 FINALIZADO! {migrados} entradas migradas, criptografadas e vetorizadas.")
    
    # Agora migra os Fatos do perfil
    cursor_sq.execute("SELECT nome, gosta_fazer, bom_em, mundo_precisa, pago_para, fatos_diversos FROM usuarios WHERE id=1")
    perfil = cursor_sq.fetchone()
    if perfil:
        n, g, b, pr, pa, f = perfil
        cur_pg.execute("""
            UPDATE users SET nome=%s, gosta_fazer=%s, bom_em=%s, mundo_precisa=%s, pago_para=%s, fatos_diversos=%s
            WHERE id=1
        """, (n, g, b, pr, pa, f))
        conn_pg.commit()
        print("👤 Perfil Ikigai e Fatos atualizados para o Admin (ID 1).")

    conn_pg.close()
    conn_sq.close()

if __name__ == "__main__":
    force_migration()
