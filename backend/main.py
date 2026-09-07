import json
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from scraper.linkedin_scraper import scrape_linkedin
from filters.job_filter import dedupe_jobs, filter_jobs, load_rules
from notifier.email_sender import notify_jobs_via_email
from notifier.telegram_sender import notify_jobs_via_telegram
from persistence import save_to_csv, save_to_html, save_to_sqlite, detect_new_jobs
from cv_parser import extract_text, analyze_cv

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


scheduler = BackgroundScheduler()
HISTORY_LIMIT = 30
# Written one directory up (the project root) by default, so opening the repo
# folder and double-clicking jobs_output.html "just works" without digging into
# backend/. Docker deployments override this via PERSISTENCE_HTML_PATH.
DEFAULT_HTML_PATH = os.path.join("..", "jobs_output.html")


def _slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return slug or "untitled"


def _pair_file_base(title, location):
    return f"jobs_output__{_slugify(title)}__{_slugify(location)}"


def _pair_path(title, location, extension):
    default_path = DEFAULT_HTML_PATH if extension == "html" else "jobs_output.csv"
    env_var = "PERSISTENCE_HTML_PATH" if extension == "html" else "PERSISTENCE_CSV_PATH"
    base_dir = os.path.dirname(os.getenv(env_var, default_path)) or "."
    return os.path.join(base_dir, f"{_pair_file_base(title, location)}.{extension}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.last_search_params = None
    app.state.history = _load_history()
    app.state.schedule_config = _load_schedule_config()
    interval_hours = float(os.getenv("SCHEDULE_INTERVAL_HOURS", "2"))
    scheduler.add_job(scheduled_run, "interval", hours=interval_hours, id="linkedin_scan", replace_existing=True)
    scheduler.start()
    print(f"Scheduler started: running every {interval_hours} hour(s)")
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def _load_history():
    history_path = os.getenv("HISTORY_PATH", "run_history.json")
    if not os.path.exists(history_path):
        return []
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_history(history):
    history_path = os.getenv("HISTORY_PATH", "run_history.json")
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history[-HISTORY_LIMIT:], f, ensure_ascii=False, indent=2)


def _load_schedule_config():
    config_path = os.getenv("SCHEDULE_CONFIG_PATH", "schedule_config.json")
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return None

    if not config or "pairs" in config:
        return config

    # migrate older formats to the current {"pairs": [{"title", "location"}]} shape
    if config.get("titles") and config.get("locations"):
        titles, locations = config["titles"], config["locations"]
        config["pairs"] = [{"title": t, "location": loc} for t in titles for loc in locations]
    elif config.get("titles") and config.get("location"):
        config["pairs"] = [{"title": t, "location": config["location"]} for t in config["titles"]]
    return config


def _save_schedule_config(config):
    config_path = os.getenv("SCHEDULE_CONFIG_PATH", "schedule_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _record_run(query, location, date_posted, experience_level, total, new_count, triggered_by):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "location": location,
        "date_posted": date_posted,
        "experience_level": experience_level,
        "total": total,
        "new_count": new_count,
        "triggered_by": triggered_by,
    }
    history = getattr(app.state, "history", None)
    if history is None:
        history = _load_history()
    history.append(entry)
    history = history[-HISTORY_LIMIT:]
    app.state.history = history
    _save_history(history)


@app.get("/")
def root():
    return {"service": "job-finder-bot-api", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/status")
def status():
    job = scheduler.get_job("linkedin_scan")
    interval_hours = float(os.getenv("SCHEDULE_INTERVAL_HOURS", "2"))
    history = getattr(app.state, "history", None) or []
    last_run = history[-1] if history else None
    return {
        "interval_hours": interval_hours,
        "next_run_at": job.next_run_time.isoformat() if job and job.next_run_time else None,
        "last_run": last_run,
        "last_search_params": getattr(app.state, "last_search_params", None),
        "schedule_config": getattr(app.state, "schedule_config", None),
    }


@app.get("/history")
def history():
    return list(reversed(getattr(app.state, "history", None) or []))


@app.get("/schedule-config")
def get_schedule_config():
    return getattr(app.state, "schedule_config", None) or {"pairs": []}


@app.post("/schedule-config")
async def set_schedule_config(request: Request):
    """Configure a fixed list of (job title, location) pairs that the every-2-hours
    auto-scan keeps searching — each pair strictly on its own (no cross-combining),
    writing its own separate CSV/HTML file — until this is called again, independent
    of whatever is typed into the manual search box."""
    body = await request.json()
    raw_pairs = body.get("pairs", [])
    pairs = []
    for p in raw_pairs:
        if not isinstance(p, dict):
            continue
        title = (p.get("title") or "").strip()
        location = (p.get("location") or "remote").strip()
        date_posted = (p.get("date_posted") or "").strip() or None
        if title:
            pairs.append({"title": title, "location": location, "date_posted": date_posted})

    if not pairs:
        return JSONResponse(content={"error": "Provide at least one (title, location) pair."}, status_code=400)

    config = {"pairs": pairs}
    app.state.schedule_config = config
    _save_schedule_config(config)
    return config


@app.post("/run-now")
def run_now():
    """Manually trigger the same search the scheduler would run next."""
    jobs = scheduled_run(triggered_by="manual")
    return JSONResponse(content=jobs)


@app.get("/run")
def run_jobs(
    query: str = "python developer",
    location: str = "remote",
    num_pages: int = 1,
    date_posted: str = "",
    experience_level: str = "",
    include_keywords: str = "",
    exclude_keywords: str = "",
):
    app.state.last_search_params = {
        "query": query,
        "location": location,
        "num_pages": num_pages,
        "date_posted": date_posted or None,
        "experience_level": experience_level or None,
        "include_keywords": include_keywords or None,
        "exclude_keywords": exclude_keywords or None,
    }
    jobs = run_all(
        query=query,
        location=location,
        num_pages=num_pages,
        date_posted=date_posted or None,
        experience_level=experience_level or None,
        include_keywords=[k.strip() for k in include_keywords.split(",") if k.strip()] or None,
        exclude_keywords=[k.strip() for k in exclude_keywords.split(",") if k.strip()] or None,
        triggered_by="manual",
    )
    return JSONResponse(content=jobs)


@app.post("/parse-cv")
async def parse_cv(file: UploadFile = File(...)):
    """Extract text from an uploaded CV (.pdf, .docx or .txt) and suggest a search query."""
    content = await file.read()
    try:
        text = extract_text(file.filename, content)
    except Exception as e:
        return JSONResponse(content={"error": f"Could not read CV: {e}"}, status_code=400)

    if not text.strip():
        return JSONResponse(content={"error": "No readable text found in the uploaded file."}, status_code=400)

    analysis = analyze_cv(text)
    return JSONResponse(content=analysis)


@app.get("/download/csv")
def download_csv():
    from fastapi.responses import FileResponse

    csv_path = os.getenv("PERSISTENCE_CSV_PATH", "jobs_output.csv")
    if not os.path.exists(csv_path):
        return JSONResponse(content={"error": "No CSV file yet. Run a search first."}, status_code=404)
    return FileResponse(csv_path, media_type="text/csv", filename="jobs_output.csv")


@app.get("/download/html")
def download_html():
    from fastapi.responses import FileResponse

    html_path = os.getenv("PERSISTENCE_HTML_PATH", DEFAULT_HTML_PATH)
    if not os.path.exists(html_path):
        return JSONResponse(content={"error": "No HTML report yet. Run a search first."}, status_code=404)
    return FileResponse(html_path, media_type="text/html", filename="jobs_output.html")


@app.get("/download/pair-html")
def download_pair_html(title: str, location: str = "remote"):
    from fastapi.responses import FileResponse

    path = _pair_path(title, location, "html")
    if not os.path.exists(path):
        return JSONResponse(content={"error": "No HTML report yet for this title/location pair."}, status_code=404)
    return FileResponse(path, media_type="text/html", filename=os.path.basename(path))


@app.get("/download/pair-csv")
def download_pair_csv(title: str, location: str = "remote"):
    from fastapi.responses import FileResponse

    path = _pair_path(title, location, "csv")
    if not os.path.exists(path):
        return JSONResponse(content={"error": "No CSV file yet for this title/location pair."}, status_code=404)
    return FileResponse(path, media_type="text/csv", filename=os.path.basename(path))


@app.post("/export")
async def export_jobs(request: Request):
    """Persist an already-merged list of jobs (e.g. combined across several
    location/title filters on the frontend) as the CSV/HTML download files,
    so downloads always match exactly what's shown on screen."""
    body = await request.json()
    jobs = body if isinstance(body, list) else body.get("jobs", [])
    if not isinstance(jobs, list):
        return JSONResponse(content={"error": "Expected a list of jobs."}, status_code=400)

    csv_path = os.getenv("PERSISTENCE_CSV_PATH", "jobs_output.csv")
    html_path = os.getenv("PERSISTENCE_HTML_PATH", DEFAULT_HTML_PATH)
    save_to_csv(jobs, csv_path)
    save_to_html(jobs, html_path)
    return {"status": "ok", "count": len(jobs)}


def run_all(
    query: str = "python developer",
    location: str = "remote",
    num_pages: int = 1,
    include_keywords=None,
    exclude_keywords=None,
    location_whitelist=None,
    enable_email=False,
    enable_telegram=False,
    date_posted=None,
    experience_level=None,
    triggered_by="manual",
    csv_path=None,
    html_path=None,
):
    queries = query if isinstance(query, list) else [query]
    locations = location if isinstance(location, list) else [location]
    all_jobs = []
    for loc in locations:
        for q in queries:
            print(f"Scraping LinkedIn for '{q}' in '{loc}'...")
            try:
                all_jobs.extend(
                    scrape_linkedin(
                        query=q,
                        location=loc,
                        num_pages=num_pages,
                        date_posted=date_posted,
                        experience_level=experience_level,
                    )
                )
            except Exception as e:
                print(f"LinkedIn scraping failed for '{q}' in '{loc}':", e)

    all_jobs = dedupe_jobs(all_jobs)
    # if rules file provided, load defaults unless explicitly passed
    rules_path = os.getenv("RULES_PATH")
    if rules_path and os.path.exists(rules_path):
        rules = load_rules(rules_path)
        if include_keywords is None:
            include_keywords = rules.get("include_keywords")
        if exclude_keywords is None:
            exclude_keywords = rules.get("exclude_keywords")
        if location_whitelist is None:
            location_whitelist = rules.get("location_whitelist")

    filtered_jobs = filter_jobs(
        all_jobs,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        location_whitelist=location_whitelist,
    )

    print(f"Total jobs: {len(all_jobs)} (after dedupe: {len(all_jobs)}, filtered: {len(filtered_jobs)})")

    output_path = os.getenv("OUTPUT_PATH", "jobs_output.json")
    state_path = os.getenv("STATE_PATH", "seen_jobs.json")
    new_only = os.getenv("NEW_ONLY", "false").lower() in ("1", "true", "yes")

    # compute new jobs vs seen state and update state
    new_jobs = detect_new_jobs(filtered_jobs, state_path=state_path)
    new_urls = {j.get("url") for j in new_jobs if j.get("url")}
    for job in filtered_jobs:
        job["is_new"] = (job.get("url") in new_urls) if job.get("url") else True

    if new_only:
        to_write = new_jobs
    else:
        to_write = filtered_jobs
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(to_write, f, ensure_ascii=False, indent=2)

    print(f"Saved {output_path} (new_only={new_only}, new_count={len(new_jobs)})")

    # Always persist results to CSV and a clickable HTML report after every run.
    # A caller (e.g. per-pair scheduled scans) may override where these land.
    csv_path = csv_path or os.getenv("PERSISTENCE_CSV_PATH", "jobs_output.csv")
    save_to_csv(filtered_jobs, csv_path)
    print(f"Saved CSV to {csv_path}")

    html_path = html_path or os.getenv("PERSISTENCE_HTML_PATH", DEFAULT_HTML_PATH)
    save_to_html(filtered_jobs, html_path)
    print(f"Saved HTML report to {html_path}")

    persistence = os.getenv("PERSISTENCE", "none").lower()
    if persistence == "sqlite":
        db_path = os.getenv("PERSISTENCE_DB_PATH", "jobs_output.db")
        save_to_sqlite(filtered_jobs, db_path)
        print(f"Saved SQLite DB to {db_path}")

    if enable_email and filtered_jobs:
        try:
            recipient_list = [email.strip() for email in os.getenv("NOTIFY_EMAILS", "").split(",") if email.strip()]
            if recipient_list:
                notify_jobs_via_email(filtered_jobs, recipient_list)
                print("Email notification sent")
            else:
                print("No receivers configured for email notification")
        except Exception as e:
            print("Email notification failed:", e)

    if enable_telegram and filtered_jobs:
        try:
            notify_jobs_via_telegram(filtered_jobs)
            print("Telegram notification sent")
        except Exception as e:
            print("Telegram notification failed:", e)

    _record_run(
        query=", ".join(queries) if isinstance(query, list) else query,
        location=", ".join(locations) if isinstance(location, list) else location,
        date_posted=date_posted,
        experience_level=experience_level,
        total=len(filtered_jobs),
        new_count=len(new_jobs),
        triggered_by=triggered_by,
    )

    return filtered_jobs


def scheduled_run(triggered_by="scheduler"):
    """Runs the LinkedIn search automatically on a recurring interval.

    Prefers an explicit /schedule-config (a fixed list of strict (title, location)
    pairs) if one has been set — that stays in effect until changed again,
    regardless of what gets typed into the manual search box. Each pair is
    searched entirely on its own (no cross-combining) and written to its own
    CSV/HTML file. Falls back to whatever was last searched manually, then to
    JOB_QUERY/JOB_LOCATION env vars.
    """
    schedule_config = getattr(app.state, "schedule_config", None)
    pairs = schedule_config.get("pairs") if schedule_config else None
    if pairs:
        print("Running scheduled LinkedIn search (schedule-config pairs):", pairs)
        all_jobs = []
        for pair in pairs:
            title, loc = pair["title"], pair.get("location") or "remote"
            all_jobs.extend(
                run_all(
                    query=title,
                    location=loc,
                    num_pages=int(os.getenv("JOB_PAGES", "1")),
                    date_posted=pair.get("date_posted"),
                    enable_email=os.getenv("ENABLE_EMAIL", "false").lower() in ("true", "1", "yes"),
                    enable_telegram=os.getenv("ENABLE_TELEGRAM", "false").lower() in ("true", "1", "yes"),
                    triggered_by=triggered_by,
                    csv_path=_pair_path(title, loc, "csv"),
                    html_path=_pair_path(title, loc, "html"),
                )
            )
        return all_jobs

    params = getattr(app.state, "last_search_params", None) or {}
    print("Running scheduled LinkedIn search (last manual search):", params)
    include_keywords = params.get("include_keywords")
    exclude_keywords = params.get("exclude_keywords")
    return run_all(
        query=params.get("query", os.getenv("JOB_QUERY", "python developer")),
        location=params.get("location", os.getenv("JOB_LOCATION", "remote")),
        num_pages=params.get("num_pages", int(os.getenv("JOB_PAGES", "1"))),
        date_posted=params.get("date_posted"),
        experience_level=params.get("experience_level"),
        include_keywords=[k.strip() for k in include_keywords.split(",") if k.strip()] if include_keywords else None,
        exclude_keywords=[k.strip() for k in exclude_keywords.split(",") if k.strip()] if exclude_keywords else None,
        enable_email=os.getenv("ENABLE_EMAIL", "false").lower() in ("true", "1", "yes"),
        enable_telegram=os.getenv("ENABLE_TELEGRAM", "false").lower() in ("true", "1", "yes"),
        triggered_by=triggered_by,
    )


if __name__ == "__main__":
    run_all(
        query=os.getenv("JOB_QUERY", "python developer"),
        location=os.getenv("JOB_LOCATION", "remote"),
        num_pages=int(os.getenv("JOB_PAGES", "1")),
        include_keywords=os.getenv("INCLUDE_KEYWORDS", "").split(",") if os.getenv("INCLUDE_KEYWORDS") else None,
        exclude_keywords=os.getenv("EXCLUDE_KEYWORDS", "").split(",") if os.getenv("EXCLUDE_KEYWORDS") else None,
        location_whitelist=os.getenv("LOCATION_WHITELIST", "").split(",") if os.getenv("LOCATION_WHITELIST") else None,
        enable_email=os.getenv("ENABLE_EMAIL", "false").lower() in ("true", "1", "yes"),
        enable_telegram=os.getenv("ENABLE_TELEGRAM", "false").lower() in ("true", "1", "yes"),
        date_posted=os.getenv("DATE_POSTED") or None,
        experience_level=os.getenv("EXPERIENCE_LEVEL") or None,
        triggered_by="cli",
    )
