import os
import json
import pandas as pd
import streamlit as st

from main import run_all


st.set_page_config(page_title="Job Finder Bot", layout="wide")
st.title("Job Finder Bot")

st.sidebar.header("Search settings")
query = st.sidebar.text_input("Query", os.getenv("JOB_QUERY", "python developer"))

# Location manager: add multiple cities and show each in a separate box
if "locations" not in st.session_state:
    # start with env default
    st.session_state["locations"] = [os.getenv("JOB_LOCATION", "remote")]

st.sidebar.subheader("Locations")
if "loc_input" not in st.session_state:
    st.session_state["loc_input"] = ""

def _add_location():
    loc = st.session_state.get("loc_input", "").strip()
    if loc and loc not in st.session_state["locations"]:
        st.session_state["locations"].append(loc)
    # clear the input
    st.session_state["loc_input"] = ""

loc_input = st.sidebar.text_input("Add a city", key="loc_input", on_change=_add_location)

# display each location in its own box with remove button
for i, loc in enumerate(list(st.session_state["locations"])):
    col1, col2 = st.sidebar.columns([4, 1])
    col1.markdown(f"**{loc}**")
    # small cross icon for remove
    if col2.button("✖", key=f"rem_{i}"):
        st.session_state["locations"].pop(i)

num_pages = st.sidebar.number_input("Pages per source", min_value=1, max_value=10, value=int(os.getenv("JOB_PAGES", "1")))
include_keywords = st.sidebar.text_input("Include keywords (comma-separated)", "")
exclude_keywords = st.sidebar.text_input("Exclude keywords (comma-separated)", "")
location_whitelist = st.sidebar.text_input("Location whitelist (comma-separated)", "")

# Job type filters (remote / in person / hybrid)
st.sidebar.header("Job type")
remote_cb = st.sidebar.checkbox("Remote", value=True)
in_person_cb = st.sidebar.checkbox("In person", value=True)
hybrid_cb = st.sidebar.checkbox("Hybrid", value=True)

def _infer_job_type(job: dict) -> str:
    """Infer job type from `location`, `title`, and `summary` fields.
    Returns one of: 'remote', 'hybrid', 'in_person'.
    """
    text = " ".join([str(job.get(k, "")) for k in ("location", "title", "summary")]).lower()
    if "hybrid" in text:
        return "hybrid"
    # common indicators for remote
    remote_indicators = ["remote", "work from home", "wfh", "telecommute"]
    for r in remote_indicators:
        if r in text:
            return "remote"
    # otherwise assume in-person / onsite
    return "in_person"

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
        results_all = []
        locations = list(st.session_state.get("locations", [])) or [os.getenv("JOB_LOCATION", "remote")]
        for loc in locations:
            res = run_all(
                query=query,
                location=loc,
                num_pages=int(num_pages),
                include_keywords=_parse_list(include_keywords) if include_keywords else None,
                exclude_keywords=_parse_list(exclude_keywords) if exclude_keywords else None,
                location_whitelist=_parse_list(location_whitelist) if location_whitelist else None,
                enable_email=enable_email,
                enable_telegram=enable_telegram,
            )
            if res:
                results_all.extend(res)

        # dedupe by url
        seen = set()
        results = []
        for j in results_all:
            u = (j.get("url") or "").strip()
            key = u or (j.get("title", "") + j.get("company", ""))
            if key in seen:
                continue
            seen.add(key)
            results.append(j)

    # apply job-type filters selected in the sidebar
    selected_types = set()
    if remote_cb:
        selected_types.add("remote")
    if hybrid_cb:
        selected_types.add("hybrid")
    if in_person_cb:
        selected_types.add("in_person")

    # filter results by inferred job type
    if selected_types and results:
        results = [j for j in results if _infer_job_type(j) in selected_types]

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
