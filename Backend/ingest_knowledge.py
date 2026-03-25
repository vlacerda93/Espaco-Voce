import os
import sys
import PyPDF2
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

# --- CONFIGURAÇÃO DE CAMINHO ---
caminho_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if caminho_base not in sys.path:
    sys.path.insert(0, caminho_base)

import Backend.banco_dados_pg as banco_dados

load_dotenv()

# 1. Configurações e Modelos
print("🧠 Carregando modelo matemático para Ingestão de Conhecimento...")
MODELO_VETOR = SentenceTransformer('all-MiniLM-L6-v2') 

def extrair_texto_pdf(caminho_pdf):
    """Lê o PDF e retorna uma lista de chunks (trechos)."""
    chunks = []
    try:
        with open(caminho_pdf, 'rb') as f:
            leitor = PyPDF2.PdfReader(f)
            for pagina in leitor.pages:
                texto = pagina.extract_text()
                if texto:
                    # Quebramos por parágrafos para a busca ser mais precisa e não explodir o prompt
                    paragrafos = [p.strip() for p in texto.split('\n\n') if len(p.strip()) > 100]
                    chunks.extend(paragrafos)
    except Exception as e:
        print(f"❌ Erro ao ler {caminho_pdf}: {e}")
    return chunks

def salvar_na_biblioteca(titulo, chunks):
    """Vetoriza cada pedaço e guarda na tabela biblioteca_teoria do PostgreSQL."""
    conn = banco_dados.get_connection()
    register_vector(conn)
    cur = conn.cursor()
    
    try:
        print(f"📦 Vetorizando {len(chunks)} fragmentos de '{titulo}'...")
        count = 0
        for trecho in chunks:
            # Transforma o texto em um vetor numérico
            vetor = MODELO_VETOR.encode(trecho).tolist()
            
            cur.execute("""
                INSERT INTO biblioteca_teoria (titulo_livro, conteudo_chunk, vetor_conhecimento)
                VALUES (%s, %s, %s)
            """, (titulo, trecho, vetor))
            count += 1
            if count % 20 == 0:
                print(f"✅ {count} fragmentos processados...")
        
        conn.commit()
        print(f"✨ Sucesso: '{titulo}' indexado com {len(chunks)} fragmentos.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao salvar '{titulo}' no banco: {e}")
    finally:
        cur.close()
        conn.close()

def iniciar_ingestao():
    pasta_docs = os.path.join(caminho_base, "Backend", "conhecimentos")
    if not os.path.exists(pasta_docs):
        print(f"Pasta {pasta_docs} não encontrada.")
        return

    arquivos = [f for f in os.listdir(pasta_docs) if f.lower().endswith(".pdf") or "artedefazer" in f.lower()]
    
    for arquivo in arquivos:
        print(f"\n📖 Iniciando: {arquivo}...")
        caminho_completo = os.path.join(pasta_docs, arquivo)
        fragmentos = extrair_texto_pdf(caminho_completo)
        
        if fragmentos:
            salvar_na_biblioteca(arquivo, fragmentos)
        else:
            print(f"⚠️ Aviso: Nenhum conteúdo extraído de {arquivo}")

if __name__ == "__main__":
    iniciar_ingestao()
