import json
from persistence import save_seen_urls, load_seen_urls, detect_new_jobs


def test_seen_urls_tmp(tmp_path):
    state = tmp_path / "seen.json"
    save_seen_urls(set(["u1"]), str(state))
    seen = load_seen_urls(str(state))
    assert "u1" in seen


def test_detect_new_jobs(tmp_path):
    state = tmp_path / "seen2.json"
    jobs = [{"url": "u1"}, {"url": "u2"}, {"url": ""}]
    # first run: both u1,u2 are new
    new = detect_new_jobs(jobs, state_path=str(state))
    assert len(new) == 3
    # second run: nothing new
    new2 = detect_new_jobs(jobs, state_path=str(state))
    assert len(new2) == 1  # the one with empty url considered new each time