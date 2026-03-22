import sys
import os
from dotenv import load_dotenv
from groq import AsyncGroq
import asyncio

# --- CONFIGURAÇÃO DE CAMINHO ---
caminho_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if caminho_base not in sys.path:
    sys.path.insert(0, caminho_base)

# --- IMPORTS ---
import Backend.banco_dados as banco_dados  


load_dotenv()
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def buscar_historico(usuario_id=1, limite=5):
    """Busca as últimas reflexões no SQLite para dar memória à IA."""
    try:
        entries = banco_dados.visualizar_reflexoes_usuario(usuario_id, limite)
        contexto = ""
        if entries:
            for data, sentimento, texto, feedback_ia in reversed(entries): 
                contexto += f"[{data}] - Humor: {sentimento}\n📝 {texto[:150]}...\n---\n"
        return contexto

    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível carregar o histórico: {e}")
        return ""

async def analisar_sentimento_e_salvar(texto_usuario, usuario_id=1, sentimento_manual="Neutro"):
    """Lê perfil e histórico, conversa com a IA e salva a nova interação no SQLite."""
    
    # 1. BUSCA DADOS DO USUÁRIO (SQLite Row)
    perfil = banco_dados.buscar_dados_usuario(usuario_id)
    if perfil:
        nome_usuario = perfil["nome"]
        gosta = perfil["gosta_fazer"]
        bom = perfil["bom_em"]
        precisa = perfil["mundo_precisa"]
        pago = perfil["pago_para"]
    else:
        nome_usuario = "Usuário"
        gosta = bom = precisa = pago = ""
    
    # 2. BUSCA A MEMÓRIA RECENTE
    memoria_passada = await buscar_historico(usuario_id, limite=5)

    # 3. MONTA O PROMPT COM CONCEITOS IKIGAI
    prompt_ikigai = (
        f"\nPerfil Ikigai de {nome_usuario}:\n"
        f"- O que gosta (Amor): {gosta}\n"
        f"- No que é bom (Talento): {bom}\n"
        f"- O que o mundo precisa (Missão): {precisa}\n"
        f"- O que pode ser pago (Renda): {pago}\n"
    )

    prompt_sistema = (
        "Você é um mentor empático do app Espaço Você. "
        f"Seu usuário é {nome_usuario}. "
        f"O usuário se sente atualmente: {sentimento_manual}. "
        f"{prompt_ikigai}"
        "\n\nHistórico recente de conversas para análise de padrões:\n"
        f"{memoria_passada}\n"
        "INSTRUÇÃO: Seu objetivo principal é ajudar o usuário a encontrar seu Ikigai. "
        "Use o histórico e os 4 pilares acima para conectar os pontos. "
        "Seja empático, identifique padrões e desafie o usuário a refletir sobre como suas ações se alinham ao seu propósito."
    )

    # 4. ENVIA PARA A GROQ (Async)
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": texto_usuario}
            ],
            model="llama-3.3-70b-versatile",
        )
        resposta_ia = chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ Erro na comunicação com a IA: {e}"

    # 5. SALVA NO BANCO DE DADOS SQLITE
    try:
        banco_dados.adicionar_reflexao_completa(
            usuario_id=usuario_id, 
            sentimento=sentimento_manual,
            texto=texto_usuario,
            feedback_ia=resposta_ia
        )
        print(f"💾 Sincronizado: Conversa com {nome_usuario} salva no SQLite!")
    except Exception as e:
        print(f"\n❌ Erro ao salvar no banco: {e}")

    return resposta_ia

if __name__ == "__main__":
    async def main():
        print(f"🚀 Testando Gerente de IA SQLite")
        entrada = "Boa noite."
        feedback = await analisar_sentimento_e_salvar(entrada, usuario_id=1, sentimento_manual="Feliz")
        print(f"\n✨ IA diz: {feedback}")
    
    asyncio.run(main())