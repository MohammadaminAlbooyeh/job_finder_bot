import time
import requests
from bs4 import BeautifulSoup
import urllib.parse

import time
import random
import os
import requests
from bs4 import BeautifulSoup
import urllib.parse


def _get_soup(url: str, max_retries: int = 3, proxies: dict | None = None):
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    ]

    env_proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    proxy_dict = proxies if proxies else ({"http": env_proxy, "https": env_proxy} if env_proxy else None)

    for attempt in range(1, max_retries + 1):
        headers = {
            "User-Agent": user_agents[(attempt - 1) % len(user_agents)],
            "Accept-Language": "en-US,en;q=0.9",
        }

        resp = requests.get(url, headers=headers, timeout=15, proxies=proxy_dict)

        if resp.status_code in (429, 403) and attempt < max_retries:
            time.sleep(2 * attempt)
            continue

        text_lower = resp.text.lower()
        if "captcha" in text_lower or "verify you're human" in text_lower or "are you a robot" in text_lower:
            raise RuntimeError("CAPTCHA detected")

        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    raise RuntimeError(f"Unable to fetch page after {max_retries} retries: {url}")


def scrape_linkedin(query: str = "software engineer", location: str = "remote", num_pages: int = 1, proxies: dict | None = None):
    """Scrape job cards from LinkedIn search results.

    - Supports optional `proxies` dict or `HTTP_PROXY`/`HTTPS_PROXY` env vars.
    - Uses rotating user agents, backoff and simple CAPTCHA detection.
    """
    jobs = []
    query_encoded = urllib.parse.quote_plus(query)
    location_encoded = urllib.parse.quote_plus(location)

    for page in range(num_pages):
        start = page * 25
        url = (
            "https://www.linkedin.com/jobs/search/"
            f"?keywords={query_encoded}&location={location_encoded}&start={start}"
        )
        soup = _get_soup(url, proxies=proxies)

        cards = soup.select("ul.jobs-search__results-list li")
        if not cards:
            cards = soup.select(".base-card")

        for card in cards:
            title_el = card.select_one("h3.base-search-card__title") or card.select_one("h3")
            company_el = card.select_one("h4.base-search-card__subtitle") or card.select_one("h4")
            location_el = card.select_one("span.job-search-card__location") or card.select_one("span")
            link_el = card.select_one("a.base-card__full-link") or card.select_one("a")

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            job_location = location_el.get_text(strip=True) if location_el else ""
            url_job = link_el["href"] if link_el and link_el.has_attr("href") else ""

            snippet_el = card.select_one("p.job-search-card__snippet")
            summary = snippet_el.get_text(strip=True) if snippet_el else ""

            jobs.append(
                {
                    "source": "linkedin",
                    "title": title,
                    "company": company,
                    "location": job_location,
                    "url": url_job,
                    "summary": summary,
                }
            )

        # human-like pause between pages
        time.sleep(random.uniform(1.0, 3.0))

    return jobs


if __name__ == "__main__":
    items = scrape_linkedin("python developer", "remote", num_pages=1)
    print(f"LinkedIn jobs: {len(items)}")
    for j in items[:5]:
        print(j)
