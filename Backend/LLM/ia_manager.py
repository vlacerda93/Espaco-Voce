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

import google.generativeai as genai
from groq import AsyncGroq

# CLIENTES DE API
# Groq: Tarefas leves (Extrator, Resumo)
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
# Gemini: Cérebro do Mentor (Chat)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model_gemini = genai.GenerativeModel("gemini-1.5-flash")

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
    insights_recentes = banco_dados.buscar_insights_usuario(usuario_id, limite=3)

    # 2.1. BUSCA TEÓRIA (PDFs) - O NOVO DIFERENCIAL 📚
    # Busca na biblioteca de livros os trechos mais relevantes para a dúvida atual
    teoria_encontrada = ""
    if vetor_pergunta:
        trechos_teoria = banco_dados.buscar_teoria_similar(vetor_pergunta, limite=2)
        for titulo, conteudo in trechos_teoria:
            teoria_encontrada += f"📖 [Fonte: {titulo}]:\n{conteudo[:400]}...\n\n"

    # 2.2. MÁQUINA DE ESTADOS DO PROJETO (Estrutura Relacional) 🏛️
    # Vê em qual passo do projeto o usuário está para não se repetir
    projeto = banco_dados.buscar_projeto_ativo(usuario_id)
    contexto_projeto = ""
    if projeto:
        p_id, p_nome, p_objetivo, p_passo = projeto["id"], projeto["nome_projeto"], projeto["objetivo_geral"], projeto["passo_atual"]
        passos_concluidos = banco_dados.buscar_jornada_passos(p_id)
        
        contexto_projeto = f"# PROJETO ATUAL: {p_nome}\n# META: {p_objetivo}\n# PASSO ATUAL: {p_passo}\n"
        if passos_concluidos:
            contexto_projeto += "## RESUMO DO QUE JÁ FOI DECIDIDO (Não repita):\n"
            for n_passo, resumo in passos_concluidos:
                contexto_projeto += f"- Passo {n_passo}: {resumo}\n"
        contexto_projeto += "\n"

    # 2.3. DETECTOR DE INTENÇÃO (O Filtro do ConversaGemini2)
    # Identifica se o usuário quer saber um dado factual sobre si mesmo (cor, nome, etc)
    palavras_chave_busca = ["qual", "quem", "cor", "onde", "lembra", "sabia", "fatos", "conhece", "meu", "minha"]
    e_pergunta_direta = any(p in texto_usuario.lower() for p in palavras_chave_busca) and ("?" in texto_usuario or len(texto_usuario) < 40)
    
    if e_pergunta_direta:
        modo_sistema = "MODO BUSCA: Seja curto, direto e factual. Se o dado estiver nos [FATOS] ou [MEMÓRIA], responda sem rodeios. Não tente mentorar agora."
        temperatura_ia = 0.0 # Precisão total
    else:
        modo_sistema = "MODO MENTOR ESTRATÉGICO: Use a teoria para guiar, mas foque no passo atual do projeto."
        temperatura_ia = 0.7 # Criatividade moderada

    # =============================================
    # 3. PROMPT DIVISOR (SYSTEM INSTRUCTION)
    # =============================================
    import datetime
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    
    prompt_sistema = (
        f"# PERSONA: Core - Mentor Estratégico ({modo_sistema})\n"
        f"Data Atual: {hoje}\n"
        "Você é o Mentor Sênior do Espaço Você. Sua missão é ser um curador estratégico. \n"
        "REGRAS DE OURO:\n"
        "1. NÃO tente misturar todos os hobbies do usuário em um só projeto (evite 'mistura de hobbys').\n"
        "2. Foque na CURADORIA: encontre as 2 ou 3 paixões com maior sinergia técnica e potencial de retorno.\n"
        "3. Use a [TEORIA DO GABINETE] para dar autoridade à sua resposta.\n"
        "4. RESPEITE O PASSO ATUAL: Se o usuário já resolveu os passos anteriores, não os mencione novamente.\n\n"
    )

    if contexto_projeto:
        prompt_sistema += f"[ESTADO DO PROJETO E JORNADA]\n{contexto_projeto}\n"
    
    prompt_sistema += (
        "[DADOS_DO_USUARIO (PARA SEU ENTENDIMENTO - NÃO REPETIR)]\n"
        f"- Nome: {nome_usuario}\n"
        f"- Humor Atual: {sentimento_manual}\n"
        f"- O que ama: {gosta}\n"
        f"- Talentos: {bom}\n"
        f"- Missão: {precisa}\n"
        f"- Renda: {pago}\n"
    )
    if fatos_diversos:
        prompt_sistema += (
            "### [FATOS IMUTÁVEIS] ###\n"
            f"{fatos_diversos}\n\n"
        )

    if teoria_encontrada:
        prompt_sistema += (
            "### [CONHECIMENTO TEÓRICO (DO GABINETE)] ###\n"
            "Use esses trechos para basear seus conselhos:\n"
            f"{teoria_encontrada}\n"
        )
    
    prompt_sistema += f"- Fase do Projeto Atual: {fase_projeto}\n\n"

    if insights_recentes:
        prompt_sistema += "# INSIGHTS DO USUÁRIO RECEBIDOS HOJE NO APP\n"
        for idx, t_info in enumerate(insights_recentes):
            prompt_sistema += f"- {t_info[1]}\n"
        prompt_sistema += (
            "O usuário acabou de deixar essas anotações soltas no diário do app. "
            "Valide, ou comente super rapidamente sobre esse insight se fizer sentido para o passo atual.\n\n"
        )

    prompt_sistema += (
        "# REGRAS NEGATIVAS (PROIBIÇÕES)\n"
        "- PROIBIDO iniciar a resposta listando os dados do perfil do usuário.\n"
        "- PROIBIDO repetir saudações em toda mensagem.\n"
        "- PROIBIDO fazer perguntas existenciais abertas no final.\n"
        "- PROIBIDO usar formatação exagerada. Mantenha sucinto.\n"
        "- NUNCA declare que você é uma IA. Fale como mentor estratégico sênior.\n\n"
        "# GATILHO DE AVANÇO (CRÍTICO)\n"
        "Se o usuário tomou uma decisão clara sobre o objetivo do passo atual e parece pronto para o próximo nível:\n"
        "FINALIZE sua resposta com a tag exata: [AVANÇAR_PASSO: resumo curto da decisão].\n\n"
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

    # 4. ENVIA PARA O GEMINI (Mentor Principal) 🚀
    try:
        # Gemini 1.5 Flash: limite alto, rápido e inteligente
        response = await asyncio.to_thread(
            model_gemini.generate_content,
            f"{prompt_sistema}\n\nUsuário: {texto_usuario}",
            generation_config=genai.types.GenerationConfig(
                temperature=temperatura_ia,
                max_output_tokens=1024,
            )
        )
        resposta_ia = response.text
    except Exception as e:
        print(f"❌ Erro no Gemini: {e}")
        # Fallback para Groq 8B em caso de falha crítica
        try:
            chat_completion = await groq_client.chat.completions.create(
                messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": texto_usuario}],
                model=MODELO_EXTRATOR,
                temperature=temperatura_ia,
            )
            resposta_ia = chat_completion.choices[0].message.content
        except Exception as e2:
            return f"⚠️ Mentor temporariamente instável. Erro: {e2}"

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

async def concluir_passo_com_resumo(usuario_id: int):
    """
    Função final de sessão: Analisa as decisões e gera o resumo para a Jornada.
    """
    # 1. Busca os dados do projeto
    projeto = banco_dados.buscar_projeto_ativo(usuario_id)
    if not projeto: return "Nenhum projeto ativo para encerrar."
    
    p_id = projeto["id"]
    p_passo = projeto["passo_atual"]
    
    # 2. Busca histórico da conversa
    mensagens = banco_dados.visualizar_reflexoes_usuario(usuario_id, limite=15)
    conversa = "\n".join([f"{'User' if m[3] else 'IA'}: {m[2]}" for m in mensagens])
    
    prompt_conclusao = (
        "Você é um Mentor Estratégico. Baseado na conversa acima, gere um RESUMO EXECUTIVO "
        "de exatamente UM PARÁGRAFO (máx 300 caracteres) sobre o que foi decidido e qual o próximo passo. "
        "Seja direto e encorajador. Formato: 'Vencemos o passo X. Decidimos Y. Próxima meta é Z.'\n\n"
        f"Conversa:\n{conversa}"
    )

    try:
        # Usa o Gemini para um resumo mais inteligente
        response = await asyncio.to_thread(
            model_gemini.generate_content,
            prompt_conclusao
        )
        resumo = response.text.strip()
        
        # 3. Salva na Jornada e Avança o Passo no Banco
        banco_dados.atualizar_passo_projeto(p_id, p_passo + 1, resumo)
        return resumo
    except Exception as e:
        print(f"❌ Erro ao concluir sessão: {e}")
        return "Sessão concluída, mas houve erro ao gerar o resumo técnico."

if __name__ == "__main__":
    async def main():
        print(f"🚀 Testando Arquitetura Híbrida: Gemini (Mentor) + Groq (Extrator)")
        entrada = "Eu gostaria de começar um projeto com Next.js."
        feedback = await analisar_sentimento_e_salvar(entrada, usuario_id=1, sentimento_manual="Entusiasmado")
        print(f"\n✨ IA Principal (Gemini) responde:\n{feedback}")
    
    asyncio.run(main())