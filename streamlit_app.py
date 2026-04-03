import os
import json
import pandas as pd
import streamlit as st

from main import run_all


st.set_page_config(page_title="Job Finder Bot", layout="wide")
st.title("Job Finder Bot — Web UI")

st.sidebar.header("Search settings")
query = st.sidebar.text_input("Query", os.getenv("JOB_QUERY", "python developer"))
location = st.sidebar.text_input("Location", os.getenv("JOB_LOCATION", "remote"))
num_pages = st.sidebar.number_input("Pages per source", min_value=1, max_value=10, value=int(os.getenv("JOB_PAGES", "1")))
include_keywords = st.sidebar.text_input("Include keywords (comma-separated)", "")
exclude_keywords = st.sidebar.text_input("Exclude keywords (comma-separated)", "")
location_whitelist = st.sidebar.text_input("Location whitelist (comma-separated)", "")

st.sidebar.header("State & rules")
rules_path = st.sidebar.text_input("Rules path (YAML)", os.getenv("RULES_PATH", ""))
state_path = st.sidebar.text_input("State path", os.getenv("STATE_PATH", "seen_jobs.json"))
new_only = st.sidebar.checkbox("Show only new jobs (NEW_ONLY)", value=False)

st.sidebar.header("Notifications")
enable_email = st.sidebar.checkbox("Enable email notifications", value=False)
enable_telegram = st.sidebar.checkbox("Enable Telegram notifications", value=False)

run_btn = st.sidebar.button("Run search")


def _parse_list(text: str):
    return [p.strip() for p in text.split(",") if p.strip()]


if run_btn:
    # propagate env-driven options used by main
    if rules_path:
        os.environ["RULES_PATH"] = rules_path
    else:
        os.environ.pop("RULES_PATH", None)

    os.environ["STATE_PATH"] = state_path
    os.environ["NEW_ONLY"] = "true" if new_only else "false"

    with st.spinner("Scraping... this may take a while"):
        results = run_all(
            query=query,
            location=location,
            num_pages=int(num_pages),
            include_keywords=_parse_list(include_keywords) if include_keywords else None,
            exclude_keywords=_parse_list(exclude_keywords) if exclude_keywords else None,
            location_whitelist=_parse_list(location_whitelist) if location_whitelist else None,
            enable_email=enable_email,
            enable_telegram=enable_telegram,
        )

    st.success(f"Search finished — {len(results)} job(s) returned")

    if results:
        df = pd.DataFrame(results)
        # some formatting
        if "summary" in df.columns:
            df["summary"] = df["summary"].astype(str)

        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="jobs.csv", mime="text/csv")

        json_str = json.dumps(results, ensure_ascii=False, indent=2)
        st.download_button("Download JSON", data=json_str, file_name="jobs.json", mime="application/json")

        st.markdown("---")
        st.header("Quick stats")
        st.write(f"Total jobs shown: {len(results)}")
    else:
        st.info("No jobs found for the current query/filters.")

st.sidebar.markdown("---")
st.sidebar.markdown("Run the bot from here or use the CLI: `python main.py`\n\nStreamlit: `streamlit run streamlit_app.py`")
