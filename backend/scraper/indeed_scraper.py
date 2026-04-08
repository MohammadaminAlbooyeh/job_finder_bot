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
        try:
            resp = requests.get(url, headers=headers, timeout=15, proxies=proxy_dict)
        except Exception:
            # network error or timeout — retry if attempts remain
            if attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            # last attempt: try Selenium fallback before failing
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from webdriver_manager.chrome import ChromeDriverManager

                options = Options()
                options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
                driver.set_page_load_timeout(30)
                driver.get(url)
                rendered = driver.page_source
                driver.quit()
                return BeautifulSoup(rendered, "html.parser")
            except Exception:
                raise RuntimeError(f"Unable to fetch page: {url}")

        if resp.status_code in (429, 403) and attempt < max_retries:
            time.sleep(2 * attempt)
            continue

        text_lower = resp.text.lower()
        if "captcha" in text_lower or "verify you're human" in text_lower or "are you a robot" in text_lower:
            # try Selenium fallback to render the page (if available)
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from webdriver_manager.chrome import ChromeDriverManager

                options = Options()
                options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
                driver.set_page_load_timeout(30)
                driver.get(url)
                rendered = driver.page_source
                driver.quit()
                return BeautifulSoup(rendered, "html.parser")
            except Exception as e:
                # try undetected-chromedriver as a stealthier fallback
                try:
                    import undetected_chromedriver as uc
                    from selenium.webdriver.chrome.options import Options as ChromeOptions
                    import shutil
                    import subprocess

                    options = ChromeOptions()
                    options.add_argument("--headless=new")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")

                    # try to detect local Chrome major version to match driver
                    version_main = None
                    chrome_paths = [
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                        "/Applications/Chromium.app/Contents/MacOS/Chromium",
                        shutil.which("google-chrome"),
                        shutil.which("chrome"),
                    ]
                    for p in chrome_paths:
                        if not p:
                            continue
                        try:
                            out = subprocess.check_output([p, "--version"], stderr=subprocess.DEVNULL)
                            out = out.decode(errors="ignore").strip()
                            # example: 'Google Chrome 146.0.7680.178'
                            parts = out.split()
                            for part in parts:
                                if part[0].isdigit():
                                    version_main = part.split(".")[0]
                                    break
                            if version_main:
                                break
                        except Exception:
                            continue

                    if version_main:
                        driver = uc.Chrome(version_main=int(version_main), options=options)
                    else:
                        driver = uc.Chrome(options=options)

                    driver.set_page_load_timeout(60)
                    driver.get(url)
                    rendered = driver.page_source
                    driver.quit()
                    return BeautifulSoup(rendered, "html.parser")
                except Exception as e2:
                    raise RuntimeError(f"CAPTCHA detected (Selenium failed: {e}; undetected-chromedriver failed: {e2})")

        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    raise RuntimeError(f"Unable to fetch page after {max_retries} retries: {url}")


def scrape_indeed(query: str = "software engineer", location: str = "remote", num_pages: int = 1, proxies: dict | None = None):
    """Scrape job cards from Indeed search results."""
    jobs = []
    query_encoded = urllib.parse.quote_plus(query)
    location_encoded = urllib.parse.quote_plus(location)

    for page in range(num_pages):
        start = page * 10
        url = (
            "https://www.indeed.com/jobs"
            f"?q={query_encoded}&l={location_encoded}&start={start}"
        )

        soup = _get_soup(url, proxies=proxies)
        cards = soup.select("div.job_seen_beacon")
        if not cards:
            cards = soup.select("div.jobsearch-SerpJobCard")

        for card in cards:
            title_el = card.select_one("h2.jobTitle") or card.select_one("a.jobtitle")
            company_el = card.select_one("span.companyName") or card.select_one("span.company")
            location_el = card.select_one("div.companyLocation") or card.select_one("div.location")
            link_el = card.select_one("a")

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            job_location = location_el.get_text(strip=True) if location_el else ""

            href = link_el["href"] if link_el and link_el.has_attr("href") else ""
            if href.startswith("/"):
                href = "https://www.indeed.com" + href

            snippet_el = card.select_one("div.job-snippet")
            summary = snippet_el.get_text(" ", strip=True) if snippet_el else ""

            jobs.append(
                {
                    "source": "indeed",
                    "title": title,
                    "company": company,
                    "location": job_location,
                    "url": href,
                    "summary": summary,
                }
            )
        # human-like pause between pages
        time.sleep(random.uniform(1.0, 3.0))

    return jobs


if __name__ == "__main__":
    items = scrape_indeed("python developer", "remote", num_pages=1)
    print(f"Indeed jobs: {len(items)}")
    for j in items[:5]:
        print(j)
