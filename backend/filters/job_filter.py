from typing import Dict, List, Optional


def filter_jobs(
    jobs: List[Dict],
    include_keywords: Optional[List[str]] = None,
    exclude_keywords: Optional[List[str]] = None,
    location_whitelist: Optional[List[str]] = None,
) -> List[Dict]:
    include_keywords = [k.lower() for k in (include_keywords or []) if k.strip()]
    exclude_keywords = [k.lower() for k in (exclude_keywords or []) if k.strip()]
    location_whitelist = [l.lower() for l in (location_whitelist or []) if l.strip()]

    def _job_text(job: Dict) -> str:
        return " ".join([str(job.get(field, "")) for field in ("title", "company", "location", "summary")]).lower()

    filtered = []
    for job in jobs:
        text = _job_text(job)

        if include_keywords and not any(kw in text for kw in include_keywords):
            continue
        if exclude_keywords and any(kw in text for kw in exclude_keywords):
            continue
        if location_whitelist and not any(loc in job.get("location", "").lower() for loc in location_whitelist):
            continue

        filtered.append(job)

    return filtered


def dedupe_jobs(jobs: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for job in jobs:
        key = (job.get("title", "").strip().lower(), job.get("company", "").strip().lower(), job.get("url", "").strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)
    return unique


def load_rules(path: str) -> Dict:
    """Load YAML rules file with keys: include_keywords, exclude_keywords, location_whitelist."""
    try:
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # coerce to lists
        def _lst(key):
            v = data.get(key)
            if v is None:
                return None
            if isinstance(v, list):
                return [str(x) for x in v]
            return [str(v)]

        return {
            "include_keywords": _lst("include_keywords"),
            "exclude_keywords": _lst("exclude_keywords"),
            "location_whitelist": _lst("location_whitelist"),
        }
    except Exception:
        return {}
