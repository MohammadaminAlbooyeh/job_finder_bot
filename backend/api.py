from typing import List, Optional
import os
import json
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from main import run_all
from persistence import load_seen_urls

app = FastAPI(title="Job Finder Bot API")


class ScrapeRequest(BaseModel):
    query: str = "python developer"
    location: str = "remote"
    num_pages: int = 1
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    location_whitelist: Optional[List[str]] = None
    enable_email: bool = False
    enable_telegram: bool = False
    run_async: bool = True


def _load_jobs(output_path: str):
    if not os.path.exists(output_path):
        return []
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scrape")
def scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Trigger a scraping run. By default runs in background (async)."""
    args = dict(
        query=request.query,
        location=request.location,
        num_pages=request.num_pages,
        include_keywords=request.include_keywords,
        exclude_keywords=request.exclude_keywords,
        location_whitelist=request.location_whitelist,
        enable_email=request.enable_email,
        enable_telegram=request.enable_telegram,
    )

    if request.run_async:
        background_tasks.add_task(run_all, **args)
        return {"status": "started"}

    jobs = run_all(**args)
    return {"status": "done", "count": len(jobs), "jobs": jobs}


@app.get("/jobs")
def get_jobs():
    output_path = os.getenv("OUTPUT_PATH", "jobs_output.json")
    jobs = _load_jobs(output_path)
    return {"count": len(jobs), "jobs": jobs}


@app.get("/jobs/new")
def get_new_jobs():
    output_path = os.getenv("OUTPUT_PATH", "jobs_output.json")
    state_path = os.getenv("STATE_PATH", "seen_jobs.json")
    jobs = _load_jobs(output_path)
    seen = load_seen_urls(state_path)
    new = []
    for job in jobs:
        url = (job.get("url") or "").strip()
        if not url or url not in seen:
            new.append(job)
    return {"count": len(new), "jobs": new}
