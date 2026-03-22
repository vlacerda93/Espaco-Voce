# Espaço Você 🌿

**Espaço Você** é um aplicativo de desenvolvimento pessoal e bem-estar projetado para ajudar os usuários a encontrar seu **Ikigai** (propósito de vida) através de reflexões guiadas por Inteligência Artificial, análise de sentimentos e uma interface intuitiva e zen.

---

## 🌸 O que é Ikigai?

O **Ikigai** é um conceito japonês que representa a razão de ser de uma pessoa — o ponto de equilíbrio entre quatro pilares fundamentais:

| Pilar | Pergunta |
|---|---|
| ❤️ O que você ama fazer | Suas paixões e interesses |
| 💪 No que você é bom | Suas habilidades e talentos |
| 🌍 O que o mundo precisa | Sua contribuição para a sociedade |
| 💰 Pelo que pode ser pago | Sua profissão ou fonte de renda |

O aplicativo guia o usuário a responder essas perguntas e usa a IA para conectar suas respostas a um propósito de vida genuíno.

---

## 🚀 Funcionalidades

- **Onboarding Personalizado**: Fluxo de boas-vindas em múltiplos passos que coleta o nome e as respostas do usuário para os 4 pilares do Ikigai. Só aparece uma vez — na primeira utilização.
- **Dashboard Principal**: Tela inicial com design premium e zen:
  - **Diagrama Ikigai Animado**: 4 círculos com animações de pulsação suave e efeito glow.
  - **Sua Jornada (Trilha)**: Visualização progresso estilo "mapa" para guiar o usuário.
  - **Diário de Insights Funcional**: Campo para salvar reflexões diárias que são persistidas no banco de dados.
  - **Modo Escuro/Claro**: Alternador no topo (Sticky Header) totalmente funcional.
- **Mentor IA com Contexto Profundo**: O chat com a IA (via Groq/Llama-3) agora lê não apenas o perfil Ikigai, mas também os **últimos 10 insights** do diário, criando uma conversa extremamente contextualizada.
- **Análise de Sentimentos**: Seleção de humor antes de cada conversa para o mentor adaptar seu tom.
- **Memória Persistente**: Banco de dados SQLite armazena o perfil Ikigai, histórico de conversas e diário de insights.
- **Design Premium & Glassmorphism**: Interface otimizada para dispositivos móveis com visual clean, transparências (blur) e micro-animações.

---

## 🛠️ Tecnologias Utilizadas

- **Frontend/Full-stack**: [Reflex](https://reflex.dev/) (framework Python para UI reativa)
- **IA / LLM**: [Groq API](https://console.groq.com/) com modelo `llama-3.3-70b-versatile`
- **Banco de Dados**: SQLite3 (via `python-sqlite3`)
- **Variáveis de Ambiente**: `python-dotenv`
- **Estilização**: Tailwind CSS v4 (integrado ao Reflex via plugins)

---

## 📂 Estrutura do Projeto

```text
espaco_voce/
├── App/                      # Frontend e servidor Reflex
│   ├── App/
│   │   └── App.py            # Código principal (UI + State + Roteamento)
│   └── rxconfig.py           # Configurações do Reflex
├── Backend/                  # Lógica de negócio
│   ├── banco_dados.py        # CRUD SQLite (usuários, diário, Ikigai)
│   └── LLM/
│       └── ia_manager.py     # Comunicação com Groq + prompt engineering
├── SQL/
│   └── espaco_voce.db        # Banco de dados SQLite
├── .agent/                   # Conhecimento e fluxos do assistente IA de dev
└── README.md
```

---

## ⚙️ Como Executar Localmente

### Pré-requisitos
- Python 3.10+
- Chave de API da [Groq](https://console.groq.com/)

### Passo a Passo

1. **Clonar o Repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd espaco_voce
   ```

2. **Configurar Ambiente Virtual**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install reflex python-dotenv groq
   ```

3. **Configurar Variáveis de Ambiente**:
   Crie um arquivo `.env` na raiz do projeto com:
   ```env
   GROQ_API_KEY=sua_chave_aqui
   ```

4. **Rodar o Aplicativo**:
   ```bash
   cd App
   ../.venv/bin/reflex run
   ```
   Acesse: `http://localhost:3000`

> **Dica:** Se a porta 3000 já estiver em uso, o Reflex usará a 3001 automaticamente. Para matar processos antigos: `pkill -f "reflex run"`

---

## 🗄️ Banco de Dados

A tabela principal `usuarios` contém o perfil Ikigai.
A tabela `diario` armazena o histórico do chat.
A tabela `insights_diario` armazena as reflexões curtas do dashboard para contexto da IA.

---

## 🏁 Realizado Hoje (22/03): **Vault UI & Interaction Focus**
- [x] **UX Grim-Zen (Fase 5)**: Design estilo "Vault Hacker" com 3 temas dinâmicos (Hacker, Low Dark, Light).
- [x] **Ciclos de Ikigai Interativos**: Círculos agora são clicáveis e exibem dados do perfil do usuário.
- [x] **Estabilidade SQLite**: Reversão estratégica de PostgreSQL para SQLite para garantir performance em hardware com 4GB RAM.
- [x] **Mentor IA Funcional**: Integração Groq/Llama-3.3 restaurada com histórico persistente no SQLite.

---

## 🛠️ Próximos Passos (Backlog)
- [ ] **Fase 4: Inteligência Local (Ollama)**: Finalizar o serviço `ia_service_pg.py` para análise comportamental sem nuvem.
- [ ] **Gráficos de Foco vs Descanso**: Integrar os últimos 7 dias de métricas em um dashboard visual.
- [ ] **Módulo de Hábitos**: Sistema de metas inteligentes sugeridas pela IA.

---

## 📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---
**ANTIGRAVITY // Espaço Você** - Seu refúgio digital de alta performance. 🌿✨

