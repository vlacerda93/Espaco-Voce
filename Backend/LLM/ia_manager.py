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
import Backend.banco_dados_pg as banco_dados  

load_dotenv()

# CLIENTES DE API
# Groq: Resolve as duas tarefas com modelos Llama
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

# --- MODELO PRINCIPAL (resposta ao usuário) ---
MODELO_PRINCIPAL = "llama-3.3-70b-versatile"
# --- MODELO LEVE (extração de fatos pela Groq) ---
MODELO_EXTRATOR = "llama-3.1-8b-instant"

# --- RAG VETORIAL (Modelos Locais Matemáticos) ---
from sentence_transformers import SentenceTransformer
try:
    modelo_vetor = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Aviso SentenceTransformer falhou: {e}")
    modelo_vetor = None


async def buscar_historico(usuario_id=1, limite=5, vetor_busca=None):
    """Busca as últimas reflexões no PostgreSQL (via Vetor se habilitado) para dar memória à IA."""
    try:
        if vetor_busca is not None and getattr(sys.modules[__name__], 'modelo_vetor', None) is not None:
            entries = banco_dados.buscar_reflexoes_similares(usuario_id, vetor_busca, limite)
        else:
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
    Extrator de Entidades da Groq (Muito Rápido): 
    Roda invisível para pescar fatos da conversa e estruturar no DB.
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
        resposta = await groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_extrator}],
            model=MODELO_EXTRATOR,
            max_tokens=150,
            temperature=0.1,
        )
        resultado = resposta.choices[0].message.content.strip()

        if resultado and resultado.upper() != "NADA":
            banco_dados.atualizar_fatos_usuario(usuario_id, resultado)
            print(f"🔍 Fatos extraídos pela Groq e salvos: {resultado[:80]}...")
        else:
            print("🔍 Groq: Nenhum fato novo detectado.")

    except Exception as e:
        print(f"⚠️ Extrator de fatos na Groq falhou (não-crítico): {e}")


async def gerar_e_salvar_resumo(usuario_id: int = 1):
    """
    Roda na última mensagem do ciclo. Lê o histórico recente e escreve
    um resumo executivo no banco para continuar o assunto amanhã.
    """
    memoria_passada = await buscar_historico(usuario_id, limite=8)
    prompt_resumo = (
        "Leia a transcrição das últimas mensagens (esta sessão) e crie UM ÚNICO PARÁGRAFO "
        "curto recapitulando qual foi a principal decisão, dúvida ou tarefa combinada. "
        "Isso servirá de memória para a próxima sessão ler e continuar o raciocínio.\n"
        "Seja super objetivo. Exemplo: 'O usuário decidiu que seu projeto será um app Next.js, "
        "mas ainda está travado no banco de dados. Prometeu fazer um rascunho de tabelas.'\n\n"
        f"Transcrições:\n{memoria_passada}"
    )
    
    try:
        resposta = await groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_resumo}],
            model=MODELO_EXTRATOR,
            max_tokens=200,
            temperature=0.3,
        )
        resultado = resposta.choices[0].message.content.strip()
        banco_dados.adicionar_trilha(usuario_id, resultado)
        print(f"🎯 Trilha (Resumo) de Sessão salva: {resultado[:80]}...")
    except Exception as e:
        print(f"⚠️ Falha ao gerar resumo da sessão: {e}")


async def analisar_sentimento_e_salvar(texto_usuario, usuario_id=1, sentimento_manual="Neutro", is_last_message=False):
    """Conversa com a IA, lendo e escrevendo no banco."""
    
    # 0. EXTRAÇÃO DE FATOS EM PARALELO
    asyncio.create_task(extrair_fatos_usuario(texto_usuario, usuario_id))
    
    # Se for a ÚLTIMA mensagem, já dispara a máquina de fazer Resumo (em paralelo)
    # Ela vai ler o histórico do banco (que ainda não tem essa exata última mensagem, mas tem a sessão toda)
    if is_last_message:
        asyncio.create_task(gerar_e_salvar_resumo(usuario_id))

    # 1. BUSCA DADOS DO USUÁRIO
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
    
    # 2. BUSCA MEMÓRIA (RAG SEMÂNTICO VETORIZADO) + FATOS DINÂMICOS
    vetor_pergunta = modelo_vetor.encode(texto_usuario).tolist() if modelo_vetor else None
    memoria_passada = await buscar_historico(usuario_id, limite=3, vetor_busca=vetor_pergunta)
    fatos_diversos = banco_dados.buscar_fatos_usuario(usuario_id)
    fase_projeto = banco_dados.buscar_fase_projeto(usuario_id)
    trilhas_passadas = banco_dados.buscar_trilhas(usuario_id, limite=4)
    insights_recentes = banco_dados.buscar_insights_usuario(usuario_id, limite=3)

    # 2.1. DETECTOR DE INTENÇÃO (O Filtro do ConversaGemini2)
    # Identifica se o usuário quer saber um dado factual sobre si mesmo (cor, nome, etc)
    palavras_chave_busca = ["qual", "quem", "cor", "onde", "lembra", "sabia", "fatos", "conhece", "meu", "minha"]
    e_pergunta_direta = any(p in texto_usuario.lower() for p in palavras_chave_busca) and ("?" in texto_usuario or len(texto_usuario) < 40)
    
    if e_pergunta_direta:
        modo_sistema = "MODO BUSCA: Seja curto, direto e factual. Se o dado estiver nos [FATOS] ou [MEMÓRIA], responda sem rodeios. Não tente mentorar agora."
        temperatura_ia = 0.0 # Precisão total
    else:
        modo_sistema = "MODO MENTOR: Seja empático, técnico e prático. Use o Ikigai como bússola."
        temperatura_ia = 0.7 # Criatividade moderada

    # =============================================
    # 3. PROMPT DIVISOR (SYSTEM INSTRUCTION)
    # =============================================
    import datetime
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    
    prompt_sistema = (
        f"# PERSONA: Core - Espaço Você ({modo_sistema})\n"
        f"Data Atual: {hoje}\n"
        "Você é o motor de inteligência do app 'Espaço Você'. "
        "Sua postura é de um Mentor Zen-Tech Sênior: direto, técnico e entusiasmado. \n"
        "Siga rigorosamente as instruções do MODO atual.\n\n"
    )

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
        prompt_sistema += (
            "### [FATOS IMUTÁVEIS - O GABINETE] ###\n"
            "Estes fatos são verdades absolutas sobre o usuário extraídas de conversas passadas. "
            "Use-os para responder perguntas diretas sobre ele:\n"
            f"{fatos_diversos}\n\n"
        )
    
    prompt_sistema += f"- Fase do Projeto Atual: {fase_projeto}\n\n"

    if trilhas_passadas:
        prompt_sistema += "# TRILHA DE CAMINHO DO USUÁRIO (SESSÕES ANTERIORES)\n"
        for idx, t_info in enumerate(reversed(trilhas_passadas)):
            prompt_sistema += f"- Degrau {idx+1}: {t_info[1]}\n"
        prompt_sistema += (
            "Este é o caminho (Trilha) do usuário até aqui. "
            "Ele evolui em passos contínuos. Entenda essa trilha e puxe ganchos. "
            "Por exemplo, 'Já que na sessão passada você fez X, hoje podíamos pensar em Y'.\n\n"
        )

    if insights_recentes:
        prompt_sistema += "# INSIGHTS DO USUÁRIO RECEBIDOS HOJE NO APP\n"
        for idx, t_info in enumerate(insights_recentes):
            prompt_sistema += f"- {t_info[1]}\n"
        prompt_sistema += (
            "O usuário acabou de deixar essas anotações soltas no diário do app e logo em seguida abriu sua conversa. "
            "Valide, ou comente super rapidamente sobre esse insight logo de cara para ele saber que você o ouviu.\n\n"
        )

    prompt_sistema += (
        "# REGRAS NEGATIVAS (PROIBIÇÕES)\n"
        "- PROIBIDO iniciar a resposta listando os dados do perfil do usuário.\n"
        "- PROIBIDO repetir saudações em toda mensagem.\n"
        "- PROIBIDO fazer perguntas existenciais abertas no final.\n"
        "- PROIBIDO usar formatação exagerada. Mantenha sucinto.\n"
        "- NUNCA declare que você é uma IA. Fale como humano mentor.\n\n"
    )

    prompt_sistema += (
        "# CONTEXTO ATUAL\n"
        f"O usuário está na fase de **{fase_projeto}** do seu projeto Ikigai.\n"
    )

    if fase_projeto == "Descoberta":
        prompt_sistema += "Ajude o usuário a identificar padrões e interseções do Ikigai fazendo perguntas técnicas claras.\n"
    elif fase_projeto == "Planejamento":
        prompt_sistema += "Cobre artefatos: planos de ação, estruturação de MVPs. O usuário agora precisa de estrutura.\n"
    elif fase_projeto == "Execução":
        prompt_sistema += "Cobre resultados palpáveis. Dê feedback prático sobre o que está sendo construído.\n"

    prompt_sistema += (
        "\nHistórico recente da conversa:\n"
        f"{memoria_passada}\n"
    )

    if is_last_message:
        prompt_sistema += (
            "\n# INSTRUÇÃO CRÍTICA DO SISTEMA\n"
            "Esta é a última mensagem do ciclo do usuário! "
            "Encerre concluindo o raciocínio. Dê um empurrão (Nudge) exigindo que ele vá para a ação agora e saia do chat.\n"
        )

    # 4. ENVIA PARA A GROQ (Async)
    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": texto_usuario}
            ],
            model=MODELO_PRINCIPAL,
            temperature=temperatura_ia,
        )
        resposta_ia = chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ Erro na comunicação com a IA: {e}"

    # 5. SALVA NO BANCO POSTGRES COM VETOR
    try:
        vetor_matematico = modelo_vetor.encode(texto_usuario).tolist() if modelo_vetor else None
        banco_dados.adicionar_reflexao_completa(
            usuario_id=usuario_id, 
            sentimento=sentimento_manual,
            texto=texto_usuario,
            feedback_ia=resposta_ia,
            vetor_matematico=vetor_matematico
        )
        print("💾 Conversa blindada e vetorizada salva no Cofre (PostgreSQL)!")
    except Exception as e:
        print(f"\n❌ Erro ao salvar no banco: {e}")

    return resposta_ia

if __name__ == "__main__":
    async def main():
        print(f"🚀 Testando Arquitetura Híbrida: Gemini (Mentor) + Groq (Extrator)")
        entrada = "Eu gostaria de começar um projeto com Next.js."
        feedback = await analisar_sentimento_e_salvar(entrada, usuario_id=1, sentimento_manual="Entusiasmado")
        print(f"\n✨ IA Principal (Gemini) responde:\n{feedback}")
    
    asyncio.run(main())