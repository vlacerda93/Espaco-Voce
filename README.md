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


## 📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---
* Espaço Você* - Plataforma de auto-educação. 🌿✨

