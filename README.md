# Espaço Você 🌿

**Espaço Você** é um aplicativo de desenvolvimento pessoal e bem-estar projetado para ajudar os usuários a encontrar seu **Ikigai** (propósito de vida) através de reflexões guiadas por Inteligência Artificial, análise de sentimentos e uma interface intuitiva e zen.

## 🚀 Funcionalidades

- **Diagrama Ikigai Interativo**: Visualize o equilíbrio entre o que você ama, no que é bom, o que o mundo precisa e pelo que pode ser pago.
- **Chat com Mentor IA**: Uma interface de chat empática onde você pode desabafar e receber insights personalizados (utilizando modelos Llama-3 via Groq).
- **Seleção de Humor**: Selecione como se sente no momento para que a IA adapte o tom da conversa.
- **Memória Persistente**: O sistema utiliza um banco de dados SQLite para lembrar de conversas passadas e evoluir com você.
- **Design Mobile-First**: Interface otimizada para dispositivos móveis com visual limpo, moderno e com efeitos de glassmorphism.

## 🛠️ Tecnologias Utilizadas

- **Frontend**: [Reflex](https://reflex.dev/) (Python-based full-stack framework)
- **Backend/IA**: Python, Groq API (Inference Engine)
- **Banco de Dados**: SQLite3
- **Estilização**: Tailwind CSS (integrado ao Reflex)

## 📂 Estrutura do Projeto

```text
espaco_voce/
├── App/                # Frontend desenvolvido em Reflex
│   ├── App/App.py      # Código principal da interface
│   └── rxconfig.py     # Configurações do Reflex
├── Backend/            # Lógica de negócio e integração com IA
│   ├── banco_dados.py  # Gerenciamento do SQLite
│   └── LLM/ia_manager.py # Comunicação com a API Groq
├── SQL/                # Arquivos de banco de dados e schemas
└── .agent/             # Fluxos de trabalho e memórias do assistente
```

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
   pip install -r App/requirements.txt
   ```

3. **Configurar Variáveis de Ambiente**:
   Crie um arquivo `.env` na raiz com sua chave:
   ```env
   GROQ_API_KEY=sua_chave_aqui
   ```

4. **Rodar o Aplicativo**:
   ```bash
   cd App
   reflex run
   ```
   Acesse: `http://localhost:3000`

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---
*Desenvolvido com carinho para o equilíbrio pessoal.*
