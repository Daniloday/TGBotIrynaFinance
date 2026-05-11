# Iryna Finance Bot

Iryna Finance Bot is a private Telegram bot for tracking shared group expenses. It stores sessions, participants, expenses, payment history, balances, and final transfers in SQLite.

## Features

- Create a group expense session with `/new`.
- Add and remove session members.
- Add expenses from plain chat messages like `-900 pizza` or `-1240 @roma bar @andrew`.
- Split expenses across all session members or selected mentioned users.
- View members, expense history, detailed balances, and final settlement transfers.
- Persist data in SQLite.
- Run in Docker and deploy to a VPS through GitHub Actions.

## Tech Stack

- Python 3.12
- aiogram 3
- SQLite
- python-dotenv
- zoneinfo/tzdata for Kyiv timezone support
- Docker
- Docker Compose
- GitHub Actions CI/CD

## Project Structure

```text
app/
  config.py                  # Environment settings
  db/                        # SQLite schema and repository
  domain/                    # Domain errors
  main.py                    # Entrypoint
  routers/                   # aiogram handlers and keyboards
  services/session.py        # Expense splitting domain logic
  state/                     # In-memory pending action state
  utils/                     # Parser, currency, timezone helpers
tests/                       # Unit tests
data/                        # Runtime SQLite storage
.github/workflows/prod.yml   # Production deploy workflow
Dockerfile                   # Bot image
docker-compose.yml           # VPS runtime setup
```

## Local Setup

Create `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
DB_PATH=data/iryna.db
```

Install and run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m app.main
```

Run tests:

```bash
python -m unittest discover -s tests
```

## Docker

```bash
docker compose up -d --build
docker compose logs -f bot
```


