import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from scraper.linkedin_scraper import scrape_linkedin
from filters.job_filter import dedupe_jobs, filter_jobs, load_rules
from notifier.email_sender import notify_jobs_via_email
from notifier.telegram_sender import notify_jobs_via_telegram
from persistence import save_to_csv, save_to_html, save_to_sqlite, detect_new_jobs
from cv_parser import extract_text, analyze_cv

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


scheduler = BackgroundScheduler()
HISTORY_LIMIT = 30


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.last_search_params = None
    app.state.history = _load_history()
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


def _record_run(query, location, job_type, date_posted, experience_level, total, new_count, triggered_by):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "location": location,
        "job_type": job_type,
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
    }


@app.get("/history")
def history():
    return list(reversed(getattr(app.state, "history", None) or []))


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
    job_type: str = "",
    date_posted: str = "",
    experience_level: str = "",
    include_keywords: str = "",
    exclude_keywords: str = "",
):
    app.state.last_search_params = {
        "query": query,
        "location": location,
        "num_pages": num_pages,
        "job_type": job_type or None,
        "date_posted": date_posted or None,
        "experience_level": experience_level or None,
        "include_keywords": include_keywords or None,
        "exclude_keywords": exclude_keywords or None,
    }
    jobs = run_all(
        query=query,
        location=location,
        num_pages=num_pages,
        job_type=job_type or None,
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

    html_path = os.getenv("PERSISTENCE_HTML_PATH", "jobs_output.html")
    if not os.path.exists(html_path):
        return JSONResponse(content={"error": "No HTML report yet. Run a search first."}, status_code=404)
    return FileResponse(html_path, media_type="text/html", filename="jobs_output.html")


def run_all(
    query: str = "python developer",
    location: str = "remote",
    num_pages: int = 1,
    include_keywords=None,
    exclude_keywords=None,
    location_whitelist=None,
    enable_email=False,
    enable_telegram=False,
    job_type=None,
    date_posted=None,
    experience_level=None,
    triggered_by="manual",
):
    print("Scraping LinkedIn...")
    try:
        all_jobs = scrape_linkedin(
            query=query,
            location=location,
            num_pages=num_pages,
            job_type=job_type,
            date_posted=date_posted,
            experience_level=experience_level,
        )
    except Exception as e:
        print("LinkedIn scraping failed:", e)
        all_jobs = []

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
    csv_path = os.getenv("PERSISTENCE_CSV_PATH", "jobs_output.csv")
    save_to_csv(filtered_jobs, csv_path)
    print(f"Saved CSV to {csv_path}")

    html_path = os.getenv("PERSISTENCE_HTML_PATH", "jobs_output.html")
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
        query=query,
        location=location,
        job_type=job_type,
        date_posted=date_posted,
        experience_level=experience_level,
        total=len(filtered_jobs),
        new_count=len(new_jobs),
        triggered_by=triggered_by,
    )

    return filtered_jobs


def scheduled_run(triggered_by="scheduler"):
    """Runs the LinkedIn search automatically on a recurring interval using the
    last parameters submitted through the API (falls back to defaults)."""
    params = getattr(app.state, "last_search_params", None) or {}
    print("Running scheduled LinkedIn search:", params)
    include_keywords = params.get("include_keywords")
    exclude_keywords = params.get("exclude_keywords")
    return run_all(
        query=params.get("query", os.getenv("JOB_QUERY", "python developer")),
        location=params.get("location", os.getenv("JOB_LOCATION", "remote")),
        num_pages=params.get("num_pages", int(os.getenv("JOB_PAGES", "1"))),
        job_type=params.get("job_type"),
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
        job_type=os.getenv("JOB_TYPE") or None,
        date_posted=os.getenv("DATE_POSTED") or None,
        experience_level=os.getenv("EXPERIENCE_LEVEL") or None,
        triggered_by="cli",
    )
