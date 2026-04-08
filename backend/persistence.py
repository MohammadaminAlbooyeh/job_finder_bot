import csv
import sqlite3
from typing import Dict, List
import json
import os


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
