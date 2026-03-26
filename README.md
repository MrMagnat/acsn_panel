# ASCN — AI Agent Platform

Платформа для управления ИИ-агентами с поддержкой воркфлоу-инструментов, автозапусков и чата.

## Стек

- **Backend**: Python 3.11, FastAPI, SQLAlchemy (async), Alembic, APScheduler
- **Frontend**: Vue 3, Vite, Pinia, Tailwind CSS
- **БД**: PostgreSQL 15
- **Кеш**: Redis 7

---

## Быстрый старт

### Требования
- Docker & Docker Compose

### Запуск

```bash
git clone <repo>
cd ascn-test
docker-compose up --build
```

После запуска:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs

### Учётная запись администратора

По умолчанию создаётся через seed в миграции:
- Email: `admin@ascn.io`
- Пароль: `admin123`

Изменить можно через переменные окружения в `docker-compose.yml`:
```yaml
ADMIN_EMAIL: admin@ascn.io
ADMIN_PASSWORD: admin123
```

---

## Переменные окружения (backend)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | postgresql+asyncpg://... | Строка подключения к PostgreSQL |
| `REDIS_URL` | redis://redis:6379/0 | Строка подключения к Redis |
| `SECRET_KEY` | change_me_in_production | Секрет для JWT токенов |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Срок жизни access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Срок жизни refresh token |
| `ADMIN_EMAIL` | admin@ascn.io | Email admin-пользователя (seed) |
| `ADMIN_PASSWORD` | admin123 | Пароль admin-пользователя (seed) |
| `SUBSCRIPTION_WEBHOOK_SECRET` | webhook_secret | Секрет для вебхука системы подписок |

---

## Интеграции с внешними сервисами

### Система подписок

При изменении тарифа пользователя внешняя система должна вызвать:

```
POST /webhooks/subscription-update
Headers: X-Webhook-Secret: <SUBSCRIPTION_WEBHOOK_SECRET>
Body:
{
  "user_id": "uuid",
  "plan": "pro",
  "max_agents": 10,
  "max_tools_per_agent": 5,
  "energy_per_week": 500
}
```

### Воркфлоу-движок

Каждый инструмент настраивается с `webhook_url`. При вызове из чата или автозапуска бэкенд отправляет:

```
POST {webhook_url}
Body:
{
  "fields": { ...заполненные_поля },
  "args": { ...аргументы_от_llm },
  "agent_id": "uuid",
  "user_id": "uuid"
}
```

Ожидаемый ответ от движка:
```json
{ "result": "...", "status": "ok" }
```

---

## Архитектура

```
/backend
  /app
    /routers     — auth, agents, tools, chat, triggers, admin, webhooks
    /services    — auth_service, agent_service, chat_service, scheduler_service
    /models      — SQLAlchemy ORM модели
    /schemas     — Pydantic схемы
    /core        — config, db, security, deps
  /alembic       — миграции

/frontend
  /src
    /pages
      /cabinet   — MyOffice, AgentDetail, Settings, ToolStore
      /admin     — Users, Agents, Tools
    /components
      /agents    — AgentCard, AddAgentModal, EditAgentModal, TriggersBlock
      /tools     — ToolCard, ToolStoreModal
      /chat      — ChatWindow
    /stores      — auth, agents, tools, toast
    /api         — http, auth, agents, tools, chat, triggers, admin
```

---

## Разработка без Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Запустить PostgreSQL и Redis локально
export DATABASE_URL="postgresql+asyncpg://ascn:ascn_secret@localhost:5432/ascn_db"
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```
