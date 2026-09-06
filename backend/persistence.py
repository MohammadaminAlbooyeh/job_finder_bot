import csv
import html
import sqlite3
from typing import Dict, List
import json
import os


def save_to_html(jobs: List[Dict], path: str):
    """Write a standalone HTML report with clickable 'Apply' links for each job."""
    rows = []
    for job in jobs:
        title = html.escape(job.get("title", ""))
        company = html.escape(job.get("company", ""))
        location = html.escape(job.get("location", ""))
        job_type = html.escape(job.get("job_type", ""))
        posted_date = html.escape(job.get("posted_date", ""))
        url = html.escape(job.get("url", ""), quote=True)
        apply_cell = f'<a class="apply" href="{url}" target="_blank" rel="noopener">Apply</a>' if url else ""
        rows.append(
            f"<tr><td>{title}</td><td>{company}</td><td>{location}</td>"
            f"<td>{job_type}</td><td>{posted_date}</td><td>{apply_cell}</td></tr>"
        )

    table_rows = "\n".join(rows) if rows else '<tr><td colspan="6">No jobs found.</td></tr>'

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Job Finder Results</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; background: #f4f6f9; color: #16202a; margin: 2rem; }}
  h1 {{ font-size: 1.3rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  th, td {{ text-align: left; padding: 0.6rem 0.9rem; border-bottom: 1px solid #e4e9ee; font-size: 0.9rem; }}
  th {{ background: #f4f6f9; }}
  a.apply {{ display: inline-block; padding: 0.35rem 0.9rem; background: #2f6fed; color: #fff; border-radius: 6px; text-decoration: none; font-weight: 600; }}
  a.apply:hover {{ background: #1f4fc4; }}
</style>
</head>
<body>
<h1>Job Finder Results ({len(jobs)} jobs)</h1>
<table>
<thead><tr><th>Title</th><th>Company</th><th>Location</th><th>Job Type</th><th>Posted</th><th>Link</th></tr></thead>
<tbody>
{table_rows}
</tbody>
</table>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)


def save_to_csv(jobs: List[Dict], path: str):
    if not jobs:
        # create empty file
        open(path, "w", encoding="utf-8").close()
        return

    keys = sorted({k for j in jobs for k in j.keys()})
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for job in jobs:
            # ensure all keys present
            row = {k: job.get(k, "") for k in keys}
            writer.writerow(row)


def save_to_sqlite(jobs: List[Dict], db_path: str, table: str = "jobs"):
    if not jobs:
        return

    keys = sorted({k for j in jobs for k in j.keys()})
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    columns_sql = ", ".join([f'"{k}" TEXT' for k in keys])
    c.execute(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_sql})")

    keys_sql = ", ".join([f'"{k}"' for k in keys])
    placeholders = ", ".join(["?" for _ in keys])
    insert_sql = f"INSERT INTO {table} ({keys_sql}) VALUES ({placeholders})"
    rows = [[str(job.get(k, "")) for k in keys] for job in jobs]
    c.executemany(insert_sql, rows)
    conn.commit()
    conn.close()


def load_seen_urls(path: str) -> set:
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data if isinstance(data, list) else [])
    except Exception:
        return set()


def save_seen_urls(urls: set, path: str):
    dirp = os.path.dirname(path)
    if dirp and not os.path.exists(dirp):
        os.makedirs(dirp, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(list(urls)), f, ensure_ascii=False, indent=2)


def detect_new_jobs(jobs: List[Dict], state_path: str = "seen_jobs.json") -> List[Dict]:
    """Return only jobs whose `url` was not seen before, and update the seen set on disk."""
    seen = load_seen_urls(state_path)
    new = []
    for job in jobs:
        url = (job.get("url") or "").strip()
        if not url:
            # consider jobs without url as new (but do not persist)
            new.append(job)
            continue
        if url in seen:
            continue
        new.append(job)
        seen.add(url)

    save_seen_urls(seen, state_path)
    return new
