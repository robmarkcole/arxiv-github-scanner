import arxiv
import re
import requests
from datetime import datetime, timedelta
import pytz

import streamlit as st
import const
import pandas as pd

utc = pytz.UTC

st.set_page_config(layout="wide")


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


def get_valid_url(text_to_search: str, regex: str) -> str:
    """
    Returns a valid url matching the regex from the abstract
    """
    matches = re.findall(regex, text_to_search)
    for url in matches:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an exception if the status code is not 200
            # print('The URL is live!')
            return url
        except requests.exceptions.HTTPError:
            pass
    return "none"


@st.experimental_memo
def convert_df(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# Settings
st.sidebar.title("Settings")
query = st.sidebar.text_input("Term to search", value=const.DEFAULT_QUERY)
max_results = st.sidebar.number_input(
    "Max search results", value=100, min_value=1, max_value=300000
)
check_for_github = st.sidebar.checkbox("Check for github link?", value=False)
check_for_zenodo = st.sidebar.checkbox("Check for zenodo link?", value=False)
filter_on_computer_vision = st.sidebar.checkbox(
    "Filter on computer vision?", value=False
)

# Get results
results = get_results(query, max_results)
parsed_results = []

# Filter results
for result in results:
    data = {
        "title": result.title,
        "published": result.published,
        "updated": result.updated,
        "primary_category": result.primary_category,
        "pdf_url": result.pdf_url,
    }
    if check_for_github:
        data["github_url"] = get_valid_url(result.summary, const.GITHUB_URL_REGEX)
    if check_for_zenodo:
        data["zenodo_url"] = get_valid_url(result.summary, const.ZENODO_URL_REGEX)
    parsed_results.append(data)

# Display results
st.title("Arxiv search results")

if len(parsed_results) > 0:
    df = pd.DataFrame(parsed_results)
    df["published"] = df["published"].dt.strftime(const.DATE_FORMAT)
    df["updated"] = df["updated"].dt.strftime(const.DATE_FORMAT)

    if filter_on_computer_vision:
        df = df[df["primary_category"] == const.COMPUTER_VISION]

    df.reset_index(drop=True, inplace=True)
    st.write(f"Number of results: {len(df)}")
    if check_for_github:
        num_github = df["github_url"].value_counts().get("none", 0)
        st.write(f"Number of results with github link: {len(df) - num_github}")
    if check_for_zenodo:
        num_zenodo = df["zenodo_url"].value_counts().get("none", 0)
        st.write(f"Number of results with zenodo link: {len(df) - num_zenodo}")

    st.dataframe(df)
    csv = convert_df(df)

    st.download_button(
        "Press to Download", csv, "arxiv.csv", "text/csv", key="download-csv"
    )
