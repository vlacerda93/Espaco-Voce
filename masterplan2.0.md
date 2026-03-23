# 📑 Master Specification: Espaço Você 2.0

**Status:** Planejamento de Arquitetura | **Versão:** 2.0.0  
**Objetivo:** Evoluir de um MVP para um Sistema de Gestão Pessoal Seguro e Inteligente.

---

## 🏗️ Fase 1: Infraestrutura e Isolamento (Docker & Network)
**Objetivo:** Criar um ambiente imutável e seguro, separando as camadas de aplicação e dados.

### 1.1 Dockerization Avançada
O objetivo é isolar a rede para que o banco de dados nunca "veja" a internet externa.
- **Serviço App:** Imagem base `python:3.11-slim`. Rodando em porta não-padrão internamente.
- **Serviço DB:** PostgreSQL 15. Persistência em volumes externos mapeados.
- **Rede (Network):** Criação de uma `frontend-network` e uma `backend-network`. O DB fica apenas na `backend-network`.

### 1.2 Configuração de Ambiente (.env)
O sistema deve ler variáveis de ambiente para:
- `SECRET_KEY`: Para hashes de sessão.
- `DB_ENCRYPTION_KEY`: Chave mestra para criptografia de dados "at rest".
- `POSTGRES_PASSWORD`: Senha de alta complexidade gerada automaticamente.

---

## 🗄️ Fase 2: Modelagem de Dados Relacional (PostgreSQL)
**Objetivo:** Abandonar arquivos estáticos por um esquema que permita análise de padrões comportamentais.

| Tabela | Campos Principais | Finalidade |
| :--- | :--- | :--- |
| **Users** | `id`, `username_hash`, `password_argon2`, `salt` | Autenticação de alta segurança. |
| **Tasks** | `id`, `user_id`, `title`, `status`, `cognitive_load (1-5)`, `deadline` | Gestão de tarefas com peso de esforço. |
| **Journal** | `id`, `user_id`, `content_encrypted`, `mood_tag`, `timestamp` | Logs de pensamentos criptografados. |
| **Metrics** | `id`, `user_id`, `type (focus/rest)`, `value`, `date` | Dados brutos para geração de gráficos de evolução. |

---

## 🔒 Fase 3: Camada de Segurança "Blue Team"
**Objetivo:** Implementar defesa ativa e proteção de dados sensíveis.

### 3.1 Criptografia Simétrica (Fernet AES-256)
Todo campo classificado como "sensível" (Diários, Reflexões) deve ser criptografado antes do `INSERT`.
- **Lógica:** O backend recebe o texto -> Criptografa usando a `DB_ENCRYPTION_KEY` -> Salva o binário no banco.
- **Recuperação:** O texto só é descriptografado no momento da renderização na tela do usuário.

### 3.2 Higiene de Código e Sanitização
- Uso obrigatório de **Pydantic** para validação de esquemas (evitando injeção de dados malformados).
- Implementação de **Middleware de Rate Limiting** (limite de 100 requisições por minuto por IP) para evitar ataques de força bruta.

---

## 🧠 Fase 4: Experiência do Usuário (UI "Grim-Zen")
**Objetivo:** Uma interface que não distraia, inspirada em terminais e estética Dark/Zen.

### 4.1 Dashboard Dinâmico
- **Widgets de Foco:** Gráficos de dispersão mostrando a relação entre "Horas de Sono" e "Tarefas Concluídas".
- **O "Cofre":** Uma área da UI protegida por re-autenticação para acessar os diários profundos.
- **Componentes:** Uso de **Reflex** para um design responsivo e customizável via temas dinâmicos (Hacker, Zen Rose, etc).

---

## 🚀 Fase 5: Roadmap de Execução (Step-by-Step)

### Etapa 1: O Esqueleto (Semana 1)
- [ ] Configurar `docker-compose.yml` com Postgres e Python.
- [ ] Implementar conexão com banco de dados usando SQLAlchemy.
- [ ] Criar sistema de Login com hash Argon2.

### Etapa 3: A Mente (Semana 2)
- [ ] Criar as rotas de CRUD para tarefas e diário.
- [ ] Implementar a classe `SecurityManager` para criptografia AES-256.
- [ ] Desenvolver o analisador de logs de erro do sistema (Monitoramento).

### Etapa 3: A Alma (Semana 3)
- [ ] Criar a lógica de "Carga Cognitiva" nas tarefas.
- [/] Refatoração completa do Frontend para o novo padrão visual (Em andamento - Temas dinâmicos e Glassmorphism OK).

---

## 🛠️ Notas para o Antigravity
> "Ao implementar este projeto, priorize sempre o Princípio do Menor Privilégio. Cada módulo deve ter acesso apenas aos dados estritamente necessários. Utilize Tipagem Estática (Type Hinting) em todo o código Python para garantir a robustez contra erros de execução."
