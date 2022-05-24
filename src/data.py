import io
import typing
import logging
import requests
import pandas as pd
import datetime as dt
import streamlit as st
from dataclasses import dataclass
from pprint import pformat

# Columns to use from Excel sheet and the corresponding column names
SOURCE_COLUMNS = "B:F,H,J,M,O,Q,R,S"
COLUMN_NAMES = [
    "posted_date",
    "date",
    "provider",
    "mrn",
    "cpt",
    "desc",
    "units",
    "wrvu",
    "charge",
    "net",
    "insurance",
    "location",
]
# Mapping from provider's short name to key in source data
ALIAS_TO_NAME = {"Lee": "Lee , Jonathan MD"}


@dataclass
class RvuData:
    # All imported data
    df: pd.DataFrame
    # Earliest posting date in data (visit date may be earlier)
    start_date: dt.date
    # Latest posting date in data
    end_date: dt.date


@dataclass
class FilteredRvuData:
    """Data extracted from RVU report and filtered for a specific provider and date range"""

    # Parameters that data in this set was filtered by
    provider: str
    start_date: dt.date
    end_date: dt.date
    # Original data set
    all: RvuData
    # Specific partitions such as inpatient encounters, WCC, etc
    partitions: dict[str, pd.DataFrame]
    # Precalculated stats, e.g. # encounters, total RVUs, etc
    stats: dict[str, typing.Any]


def fetch_file_or_url(filename_or_url):
    """Fetch source data as Excel file"""
    logging.info("Fetching " + filename_or_url)

    # Try to read as local file if url doesn't start with http
    if not filename_or_url.lower().startswith("http"):
        with open(filename_or_url, "r") as f:
            return f.read()

    # Read as URL
    with requests.get(filename_or_url, allow_redirects=True) as resp:
        logging.info(
            "Status "
            + str(resp.status_code)
            + " from "
            + resp.url
            + "\n Headers: "
            + pformat(resp.headers)
        )

        resp.raise_for_status()
        return resp.content


def excel_bytes_to_df(byts):
    """Convert Excel file to dataframe"""
    df = pd.DataFrame()
    data = pd.read_excel(
        io.BytesIO(byts),
        usecols=SOURCE_COLUMNS,
        names=COLUMN_NAMES,
        dtype={"cpt": str},
    )
    # Parse date columns
    df.posted_date = pd.to_datetime(df.posted_date, errors="coerce")
    df.date = pd.to_datetime(df.date, errors="coerce")
    # Filter out NaN values
    df = df[df.posted_date.notnull() & df.provider.notnull()]
    return df


# Use allow_output_mutation to avoid hashing return value to improve performance
# @st.cache(allow_output_mutation=True)
def fetch(filename_or_urls: list[str]) -> RvuData:
    """Main entry point: retrieve file, src, and parse into DataFrame"""
    if filename_or_urls is None:
        return None

    # Fetch all files
    df = pd.DataFrame()
    for f in filename_or_urls:
        # Read source Excel data and append into DataFrame
        byts = fetch_file_or_url(f)
        df = df.append(excel_bytes_to_df(byts))

    # Return data
    return RvuData(
        df=df, start_date=df.posted_date.min(), end_date=df.posted_date.max()
    )


def process(
    rvudata: RvuData, provider: str, start_date: dt.date, end_date: dt.date
) -> FilteredRvuData:
    """Filter data that was returned by fetch(...) and process it by partitioning it and calculating stats"""
    return RvuData(
        all=rvudata,
        provider=provider,
        start_date=start_date,
        end_date=end_date,
    )
