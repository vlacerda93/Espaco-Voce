# 🧠 Projeto Espaço Você - Brain

Este diretório contém a documentação e o conhecimento estruturado do projeto **Espaço Você**.

## 📌 Documentação Estruturada
Você pode encontrar detalhes técnicos na pasta [`.agent/knowledge`](./.agent/knowledge/):

- **[Visão Geral do Projeto](./.agent/knowledge/project_overview.md)**: O que é o Espaço Você e suas funcionalidades principais.
- **[Arquitetura do Banco de Dados](./.agent/knowledge/database_schema.md)**: Estrutura das tabelas `usuarios` e `diario`.
- **[Estratégia de Integração com IA](./.agent/knowledge/ai_integration_strategy.md)**: Como o LLM (Llama 3.3 via Groq) é configurado para ser um mentor empático.

## 🚀 Como Executar o Projeto
1. Certifique-se de que o `.env` na raiz contém uma `GROQ_API_KEY` válida.
2. Execute o script principal:
   ```bash
   python Backend/LLM/ia_manager.py
   ```
3. Para visualizar o histórico do diário no terminal:
   ```bash
   python Backend/banco_dados.py
   ```

## 🛠️ Stack Tecnológica
- **Backend:** Python
- **Banco de Dados:** SQLite
- **Modelagem de IA:** Groq (Llama 3.3 70B)
- **Gerenciamento de Ambiente:** python-dotenv
