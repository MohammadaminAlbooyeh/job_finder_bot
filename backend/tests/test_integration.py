import os
import json
from main import run_all


def test_run_all_integration(tmp_path, monkeypatch):
    # mock scrapers to return deterministic data
    def mock_linkedin(query, location, num_pages):
        return [{"source": "linkedin", "title": "L1", "company": "X", "location": "Remote", "url": "u1", "summary": "s1"}]

    def mock_indeed(query, location, num_pages):
        return [{"source": "indeed", "title": "I1", "company": "Y", "location": "Remote", "url": "u2", "summary": "s2"}]

    # patch the functions that `main` actually calls (they are imported there)
    monkeypatch.setattr("main.scrape_linkedin", mock_linkedin)
    monkeypatch.setattr("main.scrape_indeed", mock_indeed)

    out_json = tmp_path / "out.json"
    os.environ["OUTPUT_PATH"] = str(out_json)
    os.environ["PERSISTENCE"] = "csv"
    os.environ["PERSISTENCE_CSV_PATH"] = str(tmp_path / "out.csv")

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
