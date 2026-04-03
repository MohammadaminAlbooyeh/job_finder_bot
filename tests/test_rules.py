import yaml
from filters.job_filter import load_rules


def test_load_rules(tmp_path):
    p = tmp_path / "r.yaml"
    p.write_text("""
include_keywords:
  - python
exclude_keywords:
  - junior
location_whitelist:
  - remote
""")
    rules = load_rules(str(p))
    assert rules.get("include_keywords") == ["python"]
    assert rules.get("exclude_keywords") == ["junior"]
    assert rules.get("location_whitelist") == ["remote"]
