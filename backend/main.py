import json
import os
from scraper.linkedin_scraper import scrape_linkedin
from scraper.indeed_scraper import scrape_indeed
from filters.job_filter import dedupe_jobs, filter_jobs, load_rules
from notifier.email_sender import notify_jobs_via_email
from notifier.telegram_sender import notify_jobs_via_telegram
from persistence import save_to_csv, save_to_sqlite, detect_new_jobs

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/run")
def run_jobs(
    query: str = "python developer",
    location: str = "remote",
    num_pages: int = 1
):
    jobs = run_all(query=query, location=location, num_pages=num_pages)
    return JSONResponse(content=jobs)
def run_all(
    query: str = "python developer",
    location: str = "remote",
    num_pages: int = 1,
    include_keywords=None,
    exclude_keywords=None,
    location_whitelist=None,
    enable_email=False,
    enable_telegram=False,
):
    print("Scraping LinkedIn...")
    try:
        linkedin_jobs = scrape_linkedin(query=query, location=location, num_pages=num_pages)
    except Exception as e:
        print("LinkedIn scraping failed:", e)
        linkedin_jobs = []

    print("Scraping Indeed...")
    try:
        indeed_jobs = scrape_indeed(query=query, location=location, num_pages=num_pages)
    except Exception as e:
        print("Indeed scraping failed:", e)
        indeed_jobs = []

    all_jobs = linkedin_jobs + indeed_jobs
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

    # optional persistence beyond JSON
    persistence = os.getenv("PERSISTENCE", "none").lower()
    if persistence == "csv":
        csv_path = os.getenv("PERSISTENCE_CSV_PATH", "jobs_output.csv")
        save_to_csv(filtered_jobs, csv_path)
        print(f"Saved CSV to {csv_path}")
    elif persistence == "sqlite":
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
    )
