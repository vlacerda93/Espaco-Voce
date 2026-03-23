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

# --- MODELO PRINCIPAL (resposta ao usuário) ---
MODELO_PRINCIPAL = "llama-3.3-70b-versatile"
# --- MODELO LEVE (extração de fatos) ---
MODELO_EXTRATOR = "llama-3.1-8b-instant"


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


async def extrair_fatos_usuario(texto_usuario: str, usuario_id: int = 1):
    """
    Extrator de Entidades: usa um modelo leve para pegar fatos soltos
    da mensagem do usuário (cor favorita, número da sorte, nome do pet, etc.)
    e salvar no banco de dados automaticamente.
    """
    prompt_extrator = (
        "Analise o texto abaixo e extraia APENAS fatos pessoais úteis sobre o usuário. "
        "Exemplos: cor favorita, número da sorte, nome de pets, onde mora, hobbies específicos, "
        "ferramentas que usa, projetos que está desenvolvendo.\n\n"
        "REGRAS:\n"
        "- Se encontrar fatos, retorne APENAS no formato: chave: valor (um por linha)\n"
        "- Se NÃO encontrar nenhum fato novo, retorne exatamente: NADA\n"
        "- NÃO invente fatos. Extraia somente o que está explícito no texto.\n"
        "- Ignore saudações, perguntas genéricas e opiniões vagas.\n\n"
        f"TEXTO DO USUÁRIO:\n\"{texto_usuario}\""
    )

    try:
        resposta = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_extrator}],
            model=MODELO_EXTRATOR,
            max_tokens=150,
            temperature=0.1,
        )
        resultado = resposta.choices[0].message.content.strip()

        if resultado and resultado.upper() != "NADA":
            banco_dados.atualizar_fatos_usuario(usuario_id, resultado)
            print(f"🔍 Fatos extraídos e salvos: {resultado[:80]}...")
        else:
            print("🔍 Nenhum fato novo detectado.")

    except Exception as e:
        print(f"⚠️ Extrator de fatos falhou (não-crítico): {e}")


async def analisar_sentimento_e_salvar(texto_usuario, usuario_id=1, sentimento_manual="Neutro", is_last_message=False):
    """Lê perfil e histórico, conversa com a IA e salva a nova interação no SQLite."""
    
    # 0. EXTRAÇÃO DE FATOS EM PARALELO (não bloqueia a resposta principal)
    asyncio.create_task(extrair_fatos_usuario(texto_usuario, usuario_id))

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
    
    # 2. BUSCA MEMÓRIA RECENTE + FATOS DINÂMICOS + FASE
    memoria_passada = await buscar_historico(usuario_id, limite=5)
    fatos_diversos = banco_dados.buscar_fatos_usuario(usuario_id)
    fase_projeto = banco_dados.buscar_fase_projeto(usuario_id)

    # =============================================
    # 3. PROMPT DIVISOR: Persona → Dados → Regras Negativas → Contexto
    # =============================================

    # BLOCO 1: PERSONA
    prompt_sistema = (
        "# PERSONA: Mentor Zen-Tech Sênior\n"
        "Você é o Mentor Sênior do app Espaço Você. "
        "Sua postura é de colega técnico experiente: direto, entusiasmado e prático. "
        "Você orienta com base em dados concretos, identifica padrões nos desafios do usuário "
        "e sempre empurra para a AÇÃO. Substitua validação emocional por entusiasmo técnico.\n\n"
    )

    # BLOCO 2: DADOS DO USUÁRIO (injetados separadamente)
    prompt_sistema += (
        "[DADOS_DO_USUARIO]\n"
        f"- Nome: {nome_usuario}\n"
        f"- Humor Atual: {sentimento_manual}\n"
        f"- O que ama (Paixão): {gosta}\n"
        f"- No que é bom (Talento): {bom}\n"
        f"- O que o mundo precisa (Missão): {precisa}\n"
        f"- Pelo que pode ser pago (Renda): {pago}\n"
    )
    if fatos_diversos:
        prompt_sistema += f"- Fatos Pessoais Conhecidos:\n{fatos_diversos}\n"
    prompt_sistema += f"- Fase do Projeto Atual: {fase_projeto}\n\n"

    # BLOCO 3: REGRAS NEGATIVAS
    prompt_sistema += (
        "# REGRAS NEGATIVAS (PROIBIÇÕES)\n"
        "- PROIBIDO iniciar a resposta listando os dados do perfil do usuário.\n"
        "- PROIBIDO repetir saudações como 'Olá, [Nome]!' em toda mensagem.\n"
        "- PROIBIDO fazer perguntas existenciais abertas no final (ex: 'como se sente?').\n"
        "- PROIBIDO floreios desnecessários. Cada frase deve ter valor prático.\n"
        "- Use os [DADOS_DO_USUARIO] com a naturalidade de quem já conhece a pessoa há anos. "
        "Referencie fatos apenas quando forem relevantes, com sutileza.\n\n"
    )

    # BLOCO 4: CONTEXTO E INSTRUÇÕES
    prompt_sistema += (
        "# CONTEXTO & INSTRUÇÕES\n"
        f"O usuário está na fase de **{fase_projeto}** do seu projeto/jornada Ikigai.\n"
    )

    # Adapta o comportamento com base na fase
    if fase_projeto == "Descoberta":
        prompt_sistema += (
            "Nesta fase, ajude o usuário a identificar padrões, conectar interesses "
            "e descobrir as interseções do Ikigai. Faça perguntas técnicas curtas e direcionadas.\n"
        )
    elif fase_projeto == "Planejamento":
        prompt_sistema += (
            "Nesta fase, cobre artefatos concretos: planos de ação, MVPs, listas de tarefas. "
            "O usuário já se conhece; agora precisa de estrutura.\n"
        )
    elif fase_projeto == "Execução":
        prompt_sistema += (
            "Nesta fase, cobre resultados. Pergunte 'já fez?', 'qual o status?'. "
            "Dê feedback técnico sobre o que o usuário está construindo.\n"
        )
    else:
        prompt_sistema += (
            "Ajude o usuário a avançar no que for mais relevante para sua jornada.\n"
        )

    prompt_sistema += (
        "\nHistórico recente de conversas:\n"
        f"{memoria_passada}\n"
        "Use o histórico para identificar padrões e continuidade. "
        "Seja um colega sênior que direciona com coragem para a AÇÃO.\n"
    )

    # BLOCO 5: NUDGE (última mensagem do ciclo)
    if is_last_message:
        prompt_sistema += (
            "\n# INSTRUÇÃO CRÍTICA DO SISTEMA\n"
            "Esta é a oitava e última mensagem deste ciclo de conversa. "
            "Resuma o insight principal de forma instrutiva e conclusiva. "
            "Dê um empurrão amigável (Nudge) para que o usuário saia do chat e EXECUTE. "
            "Exemplo: 'Agora vai lá e testa esse script!', 'Mãos à obra — me conta depois como foi!'\n"
        )

    # 4. ENVIA PARA A GROQ (Async)
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": texto_usuario}
            ],
            model=MODELO_PRINCIPAL,
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