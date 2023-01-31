import arxiv
import re
import requests
from datetime import datetime, timedelta
import pytz

import streamlit as st
import const
import pandas as pd

utc = pytz.UTC


@st.cache()
def get_results(query: str, max_results: int) -> list:
    """
    Returns a list of arxiv results
    """
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    results = []
    for result in search.results():
        results.append(result)
    return results


def get_github_url(abstract: str) -> str:
    """
    Returns a valid github urls from the abstract, if any
    """
    matches = re.findall(const.GITHUB_URL_REGEX, abstract)
    for url in matches:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an exception if the status code is not 200
            # print('The URL is live!')
            return url
        except requests.exceptions.HTTPError:
            pass
    return ""


def process_result(result: arxiv.arxiv.Result) -> dict:
    """
    Returns a dictionary of processed result
    """
    github_url = get_github_url(result.summary)
    return {
        "title": result.title,
        "published": result.published,
        "primary_category": result.primary_category,
        "pdf_url": result.pdf_url,
        "github_url": github_url,
    }


@st.experimental_memo
def convert_df(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# Settings
st.sidebar.title("Settings")
query = st.sidebar.text_input("Term to search", value=const.DEFAULT_QUERY)
max_results = st.sidebar.number_input(
    "Max results", value=100, min_value=1, max_value=300000
)
must_be_last_7_days = st.sidebar.checkbox("Must be last 7 days?", value=False)
must_have_github = st.sidebar.checkbox("Must have github link?", value=False)
must_be_computer_science = st.sidebar.checkbox("Must be computer science?", value=False)

# Get results
results = get_results(query, max_results)
parsed_results = [process_result(result) for result in results]

# Filter results
if must_be_last_7_days:
    now = utc.localize(datetime.now())
    last_7_days = now - timedelta(days=7)
    parsed_results = [
        result for result in parsed_results if result["published"] >= last_7_days
    ]

if must_have_github:
    parsed_results = [result for result in parsed_results if result["github_url"]]

if must_be_computer_science:
    parsed_results = [
        result
        for result in parsed_results
        if result["primary_category"] == const.COMPUTER_VISION
    ]

# Display results
st.title("Arxiv results")
num_results = len(parsed_results)
st.text(f"Found {num_results} results")

if num_results > 0:
    df = pd.DataFrame(parsed_results)
    df["published"] = df["published"].dt.strftime(const.DATE_FORMAT)

    st.dataframe(df)
    csv = convert_df(df)

    st.download_button(
        "Press to Download", csv, "arxiv.csv", "text/csv", key="download-csv"
    )
