# Database Schema: Espaço Você

The project uses an SQLite database (`SQL/espaco_voce.db`) to store user data and diary interactions.

## 🗄️ Tables

### `usuarios` (Users)
Stores the profile information of the platform's users.

| Column | Type    | Description                                      |
|:-------|:--------|:------------------------------------------------|
| `id`   | INTEGER | Primary Key (Serial ID)                         |
| `nome` | TEXT    | Name of the user (e.g., "Vinícius")              |
| `email`| TEXT    | Email address for authentication/contact        |
| `plano`| TEXT    | User plan type (e.g., "Premium", "Gratuito")     |

### `diario` (Diary)
Stores the daily interactions between the user and the AI.

| Column        | Type     | Description                                               |
|:--------------|:---------|:---------------------------------------------------------|
| `id`          | INTEGER  | Primary Key                                              |
| `usuario_id`  | INTEGER  | Foreign Key (References `usuarios.id`)                   |
| `data`        | DATETIME | Timestamp of the reflection (e.g., `YYYY-MM-DD HH:MM:SS`)|
| `sentimento`  | TEXT     | Sentiment state (e.g., "Feliz", "Neutro", "Triste")      |
| `texto`       | TEXT     | User's reflection content (the diary entry)              |
| `feedback_ia` | TEXT     | AI Mentor's response/feedback based on the entry         |

---

## 🔄 Relationships
The `diario` table links to the `usuarios` table via a One-to-Many relationship on `usuario_id`.
- One user can have multiple diary entries.

## 💾 Queries
Key queries used in `banco_dados.py`:
- `buscar_dados_usuario(usuario_id)`: Fetches user info for AI prompts.
- `visualizar_reflexoes_usuario(usuario_id, limite)`: Fetches the last `N` (currently set to 12) entries to provide context to the LLM.
- `adicionar_reflexao_completa(...)`: Inserts a new entry into the `diario` table.
