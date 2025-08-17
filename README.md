# MysteriumNET-Manager

Простой менеджер узлов (агентов) на FastAPI + SQLModel + SQLite.

## Возможности
- Health-check: `GET /healthz` (Basic Auth не требуется)
- Админ UI (Basic Auth): `/ui/admin`, `/ui/deployer`, `/ui/stats`
- Регистрация агента: `POST /agents/register` (заголовок `X-Manager-Secret` обязателен)
- Базовый удалённый деплой агента по SSH из `/ui/deployer`

## Быстрый старт (Docker Compose)
```bash
# В корне репозитория:
cp .env.example .env
# Поменяйте ADMIN_PASSWORD и MANAGER_SECRET
docker compose up -d --build
curl -s http://127.0.0.1:8080/healthz
# → {"status":"ok"}
```

UI: `http://<IP>:${MANAGER_PORT:-8080}/ui/admin` (Basic Auth = ADMIN_USER / ADMIN_PASSWORD)

## Переменные окружения
- `ADMIN_USER`, `ADMIN_PASSWORD` — логин/пароль для UI
- `MANAGER_SECRET` — общий секрет; агент должен присылать его в заголовке `X-Manager-Secret`
- `DATABASE_URL` — по умолчанию `sqlite:////data/manager.db`
- `MANAGER_PORT` — порт HTTP (по умолчанию 8080)
- `AGENT_REPO_URL` — репозиторий агента для удалённого деплоя

## API
### `GET /healthz`
Возвращает `{"status":"ok"}`.

### `POST /agents/register`
Заголовок: `X-Manager-Secret: <MANAGER_SECRET>`  
Тело (JSON):
```json
{"agent_name":"agent-1","wallet_address":"0x...","host":"1.2.3.4","version":"1.0.0"}
```
Ответ: `{"ok": true}` и агент отображается на странице `/ui/stats`.

### `POST /agents/deploy` (из UI)
Форма принимает `host`, `ssh_user`, `ssh_pass` (или пусто, если собираетесь ключом), `wallet_address`, `agent_name`.

> Для продвинутого сценария с автоконфигурированием root/ssh-ключа добавьте свою логику в `app/routers/agents.py` и/или `scripts/`.

## Структура
```
app/
  main.py, db.py, models.py, security.py
  routers/agents.py, routers/ui.py
  templates/*.html
  static/css/styles.css
scripts/
  install_manager_one_command.sh
  prepare_remote_root_access.sh
  remote_deploy_agent.sh
Dockerfile
docker-compose.yml
.env.example
```

## One-line installer
Скрипт в `scripts/install_manager_one_command.sh` предназначен для запуска через curl|bash **из этого репозитория**.
