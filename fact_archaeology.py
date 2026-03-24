import os
import sys
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

# --- CONFIGURAÇÃO DE CAMINHO ---
caminho_base = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if caminho_base not in sys.path:
    sys.path.insert(0, caminho_base)

import Backend.banco_dados_pg as banco_dados

load_dotenv()
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_EXTRATOR = "llama-3.1-8b-instant"

async def extrair_fatos_retroativos(usuario_id=1):
    print("🐕 Farejando fatos em todo o histórico de 85 mensagens...")
    
    # 1. Pega todas as mensagens descriptografadas
    mensagens = banco_dados.visualizar_reflexoes_usuario(usuario_id, limite=100)
    
    # Vamos processar em blocos para economizar tokens/contexto
    blocos = []
    chunk_size = 15 # Agrupa 15 mensagens por vez para a IA analisar de uma lapada só
    for i in range(0, len(mensagens), chunk_size):
        texto_bloco = ""
        for m in mensagens[i:i+chunk_size]:
            texto_bloco += f"Usuário: {m[2]}\n"
        blocos.append(texto_bloco)

    print(f"📦 Dividido em {len(blocos)} blocos de histórico.")
    
    for idx, bloco in enumerate(blocos):
        print(f"📝 Processando bloco {idx+1}/{len(blocos)}...")
        prompt = (
            "Analise as seguintes mensagens e extraia APENAS fatos pessoais imutáveis do usuário. "
            "Exemplos: Cor favorita, pets, hobbies, ferramentas que usa, curso que faz, onde mora.\n\n"
            "Retorne APENAS no formato: chave: valor (um por linha)\n"
            "Se nada for encontrado, retorne: NADA\n\n"
            f"HISTÓRICO:\n{bloco}"
        )
        
        try:
            resp = await groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_EXTRATOR,
                temperature=0.1
            )
            resultado = resp.choices[0].message.content.strip()
            if resultado and resultado.upper() != "NADA":
                banco_dados.atualizar_fatos_usuario(usuario_id, resultado)
                print(f"✨ Fatos novos encontrados: {resultado[:50]}...")
        except Exception as e:
            print(f"❌ Erro no bloco {idx+1}: {e}")
            
    print("🎉 Histórico totalmente farejado e fatos consolidados no Gabinete!")

if __name__ == "__main__":
    asyncio.run(extrair_fatos_retroativos())
