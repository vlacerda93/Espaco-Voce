import os
import sys

# --- CONFIGURAÇÃO DE CAMINHO ---
caminho_base = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if caminho_base not in sys.path:
    sys.path.insert(0, caminho_base)

import Backend.banco_dados_pg as banco_dados
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector

print("🧠 Iniciando Processamento de Vetores Retroativos...")

# 1. Carrega o modelo
modelo_vetor = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Busca reflexões sem vetor
conn = banco_dados.get_connection()
register_vector(conn)
cur = conn.cursor()

cur.execute("SELECT id, texto_encrypted FROM journal WHERE vetor_mensagem IS NULL")
rows = cur.fetchall()

if not rows:
    print("✅ Todas as mensagens já estão vetorizadas!")
    sys.exit()

print(f"📦 Encontradas {len(rows)} mensagens para processar.")

for row_id, texto_encri in rows:
    try:
        # Descriptografa para poder vetorizar o texto puro
        texto_puro = banco_dados.security.decrypt_data(bytes(texto_encri).decode())
        
        # Gera o vetor
        vetor = modelo_vetor.encode(texto_puro).tolist()
        
        # Salva no banco
        cur.execute("UPDATE journal SET vetor_mensagem = %s WHERE id = %s", (vetor, row_id))
        print(f"✅ Vetorizado ID {row_id}")
    except Exception as e:
        print(f"❌ Erro no ID {row_id}: {e}")

conn.commit()
cur.close()
conn.close()
print("🎉 Processamento concluído!")
