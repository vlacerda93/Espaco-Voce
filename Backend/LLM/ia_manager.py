import sys
import os
from dotenv import load_dotenv
from groq import AsyncGroq
import asyncio

# --- CONFIGURAÇÃO DE CAMINHO ---
caminho_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if caminho_base not in sys.path:
    sys.path.insert(0, caminho_base)

# --- IMPORTS ---
import banco_dados  

load_dotenv()
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def buscar_historico(usuario_id=1, limite=12):
    """Busca as últimas reflexões no banco para dar memória à IA."""
    try:
        # Nota: O sqlite3 em si é síncrono, mas o volume de dados é pequeno.
        # Em uma escala maior, usaríamos aiosqlite.
        historico = banco_dados.visualizar_reflexoes_usuario(usuario_id, limite)
        contexto = ""
        if historico:
            for h in reversed(historico): 
                contexto += f"Usuário: {h[2]}\nIA: {h[3]}\n---\n"
        return contexto
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível carregar o histórico: {e}")
        return ""

async def analisar_sentimento_e_salvar(texto_usuario, usuario_id=1, sentimento_manual="Neutro"):
    """Lê perfil e histórico, conversa com a IA e salva a nova interação."""
    
    # 1. BUSCA DADOS DO USUÁRIO
    perfil = banco_dados.buscar_dados_usuario(usuario_id)
    nome_usuario = perfil['nome'] if perfil else "Usuário"
    
    # 2. BUSCA A MEMÓRIA RECENTE
    memoria_passada = await buscar_historico(usuario_id, limite=12)
    
    # 3. MONTA O PROMPT COM CONCEITOS IKIGAI
    prompt_ikigai = ""
    if perfil and perfil['gosta_fazer']:
        prompt_ikigai = (
            f"\nPerfil Ikigai de {nome_usuario}:\n"
            f"- O que gosta (Amor): {perfil['gosta_fazer']}\n"
            f"- No que é bom (Talento): {perfil['bom_em']}\n"
            f"- O que o mundo precisa (Missão): {perfil['mundo_precisa']}\n"
            f"- O que pode ser pago (Renda): {perfil['pago_para']}\n"
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
        "Seja empático, mas desafie o usuário a refletir sobre seu propósito."
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

    # 5. SALVA NO BANCO DE DADOS
    try:
        banco_dados.adicionar_reflexao_completa(
            usuario_id=usuario_id, 
            sentimento=sentimento_manual, 
            texto=texto_usuario, 
            feedback_ia=resposta_ia
        )
        print(f"💾 Sincronizado: Conversa com {nome_usuario} salva no banco!")
    except Exception as e:
        print(f"\n❌ Erro ao salvar no banco: {e}")

    return resposta_ia

# --- EXECUÇÃO DE TESTE ---
if __name__ == "__main__":
    async def main():
        perfil_inicial = banco_dados.buscar_dados_usuario(1)
        nome = perfil_inicial['nome'] if perfil_inicial else "Vinícius"
        print(f"🚀 Testando Gerente de IA Async (Usuário: {nome})")
        entrada = "Hoje me senti muito produtivo mas cansado."
        feedback = await analisar_sentimento_e_salvar(entrada, usuario_id=1, sentimento_manual="Feliz")
        print(f"\n✨ IA diz: {feedback}")
    
    asyncio.run(main())