## Project Structure & Module Organization
- `app/main.py` - bot entrypoint: loads settings, initializes SQLite, registers aiogram routers, and starts polling.
- `app/config.py` - environment loading. Required: `BOT_TOKEN`; optional: `DB_PATH` with default `data/iryna.db`.
- `app/db/` - SQLite schema and repository.
  - `schema.py` - tables and indexes.
  - `repo.py` - session, participant, expense, history, and balance persistence.
- `app/services/session.py` - in-memory expense splitting domain model and transfer calculation.
- `app/routers/` - aiogram command, message, and callback handlers.
  - `sessions/` - `/new`, session creation and confirmation.
  - `balances/` - `/check`, balance details, and navigation callbacks.
  - `expenses.py`, `history.py`, `members.py`, `start.py` - expense input, history, members, and help.
- `app/utils/` - parsing, currency formatting, and Kyiv timezone helpers.
- `tests/` - unit tests for parser, domain calculations, SQLite repository, and rendering helpers.
- `data/` - runtime SQLite storage, mounted in Docker. Do not commit runtime DB files.
- `.github/workflows/prod.yml` - production deploy workflow.
- `Dockerfile`, `docker-compose.yml` - production container build and runtime setup.

## Run Locally
1. Create `.env` from `.env.example`.
2. Install the project:
   `pip install -e .`
3. Start the bot:
   `python -m app.main`

## Run Tests
- Local:
  `python -m unittest discover -s tests`
- Docker:
  `docker build -t tgbot-iryna-finance:test .`
  `docker run --rm tgbot-iryna-finance:test python -m unittest discover -s tests`

## Docker Runtime
- Start:
  `docker compose up -d --build`
- Logs:
  `docker compose logs -f bot`
- The SQLite database must be available at `./data/iryna.db` by default.

## Deployment
- Production deploys run from tags that start with `v`.
- The workflow verifies that the tagged commit belongs to `origin/prod`.
- Normal release flow:
  `git checkout prod`
  `git merge dev --ff-only`
  `git push origin prod`
  `git tag -a v1.2.0 -m "Release v1.2.0"`
  `git push origin v1.2.0`
