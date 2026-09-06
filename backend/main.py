import json
import os
from contextlib import asynccontextmanager

from scraper.linkedin_scraper import scrape_linkedin
from filters.job_filter import dedupe_jobs, filter_jobs, load_rules
from notifier.email_sender import notify_jobs_via_email
from notifier.telegram_sender import notify_jobs_via_telegram
from persistence import save_to_csv, save_to_sqlite, detect_new_jobs
from cv_parser import extract_text, analyze_cv

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
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

@app.get("/")
def root():
    return {"service": "job-finder-bot-api", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/run")
def run_jobs(
    query: str = "python developer",
    location: str = "remote",
    num_pages: int = 1,
    job_type: str = "",
    date_posted: str = "",
):
    app.state.last_search_params = {
        "query": query,
        "location": location,
        "num_pages": num_pages,
        "job_type": job_type or None,
        "date_posted": date_posted or None,
    }
    jobs = run_all(
        query=query,
        location=location,
        num_pages=num_pages,
        job_type=job_type or None,
        date_posted=date_posted or None,
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
):
    print("Scraping LinkedIn...")
    try:
        all_jobs = scrape_linkedin(
            query=query,
            location=location,
            num_pages=num_pages,
            job_type=job_type,
            date_posted=date_posted,
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
    if new_only:
        to_write = new_jobs
    else:
        to_write = filtered_jobs
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(to_write, f, ensure_ascii=False, indent=2)

    print(f"Saved {output_path} (new_only={new_only}, new_count={len(new_jobs)})")

    # Always persist results to CSV so a downloadable file is available after every run.
    csv_path = os.getenv("PERSISTENCE_CSV_PATH", "jobs_output.csv")
    save_to_csv(filtered_jobs, csv_path)
    print(f"Saved CSV to {csv_path}")

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

    return filtered_jobs


def scheduled_run():
    """Runs the LinkedIn search automatically on a recurring interval using the
    last parameters submitted through the API (falls back to defaults)."""
    params = getattr(app.state, "last_search_params", None) or {}
    print("Running scheduled LinkedIn search:", params)
    run_all(
        query=params.get("query", os.getenv("JOB_QUERY", "python developer")),
        location=params.get("location", os.getenv("JOB_LOCATION", "remote")),
        num_pages=params.get("num_pages", int(os.getenv("JOB_PAGES", "1"))),
        job_type=params.get("job_type"),
        date_posted=params.get("date_posted"),
        enable_email=os.getenv("ENABLE_EMAIL", "false").lower() in ("true", "1", "yes"),
        enable_telegram=os.getenv("ENABLE_TELEGRAM", "false").lower() in ("true", "1", "yes"),
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
    )
