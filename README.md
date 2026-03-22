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
- **Dashboard Principal**: Tela inicial com:
  - Diagrama Ikigai visual (4 círculos sobrepostos com bolha central)
  - Card "Biblioteca de Sessões" com caminhos guiados
  - Card "Diário de Insights" para reflexões do dia
  - Botão **"Start Journey"** para iniciar a conversa com o Mentor IA
- **Mentor IA com Memória de Propósito**: O chat com a IA (via Groq/Llama-3) recebe automaticamente o perfil Ikigai do usuário no contexto, tornando cada resposta personalizada e conectada ao propósito de vida.
- **Análise de Sentimentos**: Seleção de humor antes de cada conversa para o mentor adaptar seu tom.
- **Memória Persistente**: Banco de dados SQLite armazena o perfil Ikigai e o histórico de conversas.
- **Design Mobile-First**: Interface otimizada para dispositivos móveis com visual clean, glassmorphism e micro-animações.
- **Roteamento**: Página principal (`/`) com o dashboard e página de chat (`/chat`) separada.

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

A tabela principal `usuarios` contém:

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER | Identificador único |
| `nome` | TEXT | Nome do usuário |
| `gosta_fazer` | TEXT | Pilar: O que ama fazer |
| `bom_em` | TEXT | Pilar: No que é bom |
| `mundo_precisa` | TEXT | Pilar: O que o mundo precisa |
| `pago_para` | TEXT | Pilar: Pelo que pode ser pago |

A tabela `diario` armazena cada interação do usuário com o Mentor IA.

---

## 🔐 Segurança (próximos passos)

- Implementar autenticação de usuários (login/senha ou OAuth)
- Sanitizar entradas do usuário antes de enviar à IA
- Rate limiting no endpoint do chat para evitar abuso da API

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---
*Desenvolvido com carinho para o equilíbrio pessoal. 🌸*
