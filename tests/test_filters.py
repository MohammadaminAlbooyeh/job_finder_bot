from filters.job_filter import filter_jobs, dedupe_jobs


def sample_jobs():
    return [
        {"title": "Python Developer", "company": "A", "location": "Remote", "url": "1", "summary": "backend"},
        {"title": "Senior Python Developer", "company": "B", "location": "NY", "url": "2", "summary": "fullstack"},
        {"title": "Python Developer", "company": "A", "location": "Remote", "url": "1", "summary": "backend"},
    ]


def test_dedupe_jobs():
    jobs = sample_jobs()
    unique = dedupe_jobs(jobs)
    assert len(unique) == 2


def test_filter_include_exclude():
    jobs = sample_jobs()
    inc = filter_jobs(jobs, include_keywords=["senior"])  # only senior
    assert len(inc) == 1

    exc = filter_jobs(jobs, exclude_keywords=["senior"])  # remove senior
    assert all("senior" not in (j["title"].lower() + j["summary"].lower()) for j in exc)


def test_location_whitelist():
    jobs = sample_jobs()
    wh = filter_jobs(jobs, location_whitelist=["remote"])  # only remote
    assert all("remote" in j["location"].lower() for j in wh)
