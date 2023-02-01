import arxiv
import re
import requests
from datetime import datetime, timedelta
import pytz

import streamlit as st
import const
import pandas as pd

from st_aggrid import AgGrid, JsCode, GridOptionsBuilder

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


@st.cache()
def parse_results(results: list) -> list:
    """
    Returns a list of parsed results
    """
    parsed_results = []
    for result in results:
        data = {
            "title": result.title,
            "published": result.published.strftime(const.DATE_FORMAT),
            "primary_category": result.primary_category,
            "pdf_url": result.pdf_url,
            "github_url": get_valid_url(result.summary, const.GITHUB_URL_REGEX),
        }
        parsed_results.append(data)
    return parsed_results


@st.cache()
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
    return ""


@st.experimental_memo
def convert_df(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# Settings
st.sidebar.title("Settings")
query = st.sidebar.text_input("Term to search", value=const.DEFAULT_QUERY)
max_results = st.sidebar.number_input(
    "Max search results", value=100, min_value=1, max_value=300000
)
query_on_computer_vision = st.sidebar.checkbox(
    "Query on computer vision (cs.CV)?", value=True
)

if query_on_computer_vision:
    query += f" AND cat:{const.COMPUTER_VISION}"

# Get results
results = get_results(query, max_results)
parsed_results = parse_results(results)

# Display results
st.title("Arxiv search results")

if len(parsed_results) > 0:
    df = pd.DataFrame(parsed_results)
    st.write(f"Number of results: {len(df)}")
    num_github = df["github_url"].value_counts().get("", 0)
    st.write(f"Number of results with github link: {len(df) - num_github}")
    csv = convert_df(df)

    st.download_button(
        "Press to Download", csv, "arxiv.csv", "text/csv", key="download-csv"
    )

    # st.dataframe(df)

    # AgGrid
    gb = GridOptionsBuilder.from_dataframe(df)

    cell_renderer = JsCode(
        """
            function(params) {
                return '<a href=' + params.value + ' target="_blank">'+ params.value +'</a>'
                }
            """
    )

    gb.configure_column(
        "pdf_url",
        headerName="pdf_url",
        cellRenderer=cell_renderer,
    )

    gb.configure_column(
        "github_url",
        headerName="github_url",
        cellRenderer=cell_renderer,
    )

    gridOptions = gb.build()

    AgGrid(df, gridOptions=gridOptions, allow_unsafe_jscode=True)
