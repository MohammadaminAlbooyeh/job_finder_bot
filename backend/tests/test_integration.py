import os
import json
from main import run_all


def test_run_all_integration(tmp_path, monkeypatch):
    # mock scraper to return deterministic data
    def mock_linkedin(query, location, num_pages, job_type=None, date_posted=None):
        return [{"source": "linkedin", "title": "L1", "company": "X", "location": "Remote", "url": "u1", "summary": "s1"}]

    # patch the function that `main` actually calls (it is imported there)
    monkeypatch.setattr("main.scrape_linkedin", mock_linkedin)

    out_json = tmp_path / "out.json"
    os.environ["OUTPUT_PATH"] = str(out_json)
    os.environ["PERSISTENCE"] = "csv"
    os.environ["PERSISTENCE_CSV_PATH"] = str(tmp_path / "out.csv")
    os.environ["STATE_PATH"] = str(tmp_path / "seen.json")
    os.environ["HISTORY_PATH"] = str(tmp_path / "history.json")

    results = run_all(query="q", location="l", num_pages=1, enable_email=False, enable_telegram=False)
    assert isinstance(results, list)

    # check JSON saved
    with open(out_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) >= 1

    # cleanup env
    os.environ.pop("OUTPUT_PATH", None)
    os.environ.pop("PERSISTENCE", None)
    os.environ.pop("PERSISTENCE_CSV_PATH", None)
    os.environ.pop("STATE_PATH", None)
    os.environ.pop("HISTORY_PATH", None)
