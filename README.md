Job Finder Bot
===============

Simple job scraping runner that collects results from LinkedIn and Indeed, supports filtering, deduplication, notifications and optional persistence.

Usage
-----

Run locally:

```bash
python main.py
```

Environment variables
---------------------

- `JOB_QUERY` — search query (default: `python developer`)
- `JOB_LOCATION` — location (default: `remote`)
- `JOB_PAGES` — number of pages per source (default: `1`)
- `OUTPUT_PATH` — JSON output path (default: `jobs_output.json`)
- `PERSISTENCE` — `none` | `csv` | `sqlite` (default: `none`)
- `PERSISTENCE_CSV_PATH` — CSV path when `PERSISTENCE=csv` (default: `jobs_output.csv`)
- `PERSISTENCE_DB_PATH` — SQLite DB path when `PERSISTENCE=sqlite` (default: `jobs_output.db`)

Notification envs
-----------------

- `ENABLE_EMAIL` — enable email sending (`true`/`false`)
- `NOTIFY_EMAILS` — comma-separated recipient emails
- `EMAIL_FROM`, `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- `ENABLE_TELEGRAM` — enable Telegram sending (`true`/`false`)
- `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`

Proxy & scraping
-----------------

Set `HTTP_PROXY` or `HTTPS_PROXY` to route scraping traffic through a proxy. The scrapers rotate user-agents, back off on 429/403 and attempt simple CAPTCHA detection — if a CAPTCHA is detected the scraper raises `RuntimeError`.

Tests
-----

Run tests with `pytest`:

```bash
pip install -r requirements.txt
pytest -q
```
