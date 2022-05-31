import io
import re
import typing
import logging
import requests
import pandas as pd
import datetime as dt
import streamlit as st
from . import data_files
from dataclasses import dataclass
from pprint import pformat

# Columns to use from Excel sheet and the corresponding column names
SOURCE_COLUMNS = "B,C,D,E,G,H,I,K,N,P,R,S,T"
COLUMN_NAMES = [
    "posted_date",
    "date",
    "provider",
    "mrn",
    "visitid",
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
ALIAS_TO_NAME = {
    "Lee": "Lee , Jonathan MD",
    "Mike": "Frostad, Michael J. MD",
    "Gordon": "Gordon, Methuel A. MD",
    "Katie": "Hryniewicz, Kathryn N. MD",
    "Shields": "Shields, Maricarmen S. MD",
}
# Specific location strings that indicate an inpatient charge
INPT_LOCATIONS = ["Pullman Regional Hospital IP", "Pullman Regional Hospital OP"]
# Regex matching outpatient procedure CPT codes
RE_PROCEDURE_CODES = "54150|41010|120[01][1-8]"


@dataclass(eq=True, frozen=True)
class RvuData:
    """Data extracted from RVU report from EMR and partitioned by provider"""

    # All imported data
    df: pd.DataFrame
    # Earliest posting date in data (visit date may be earlier)
    start_date: dt.date
    # Latest posting date in data
    end_date: dt.date
    # DataFrames for each provider's data
    by_provider: dict[str, pd.DataFrame]


@dataclass
class FilteredRvuData:
    """
    RvuData that has been further filtered by a specified provider and date range,
    with meaningful partitions and statistics used for the dashboard.
    """

    # Parameters that data in this set was filtered by
    provider: str
    start_date: dt.date
    end_date: dt.date
    # Original data set
    all: RvuData
    # Data set for this provider and date range
    df: pd.DataFrame
    # Specific partitions such as inpatient encounters, WCC, etc
    partitions: dict[str, pd.DataFrame]
    # Precalculated stats, e.g. # encounters, total RVUs, etc
    stats: dict[str, typing.Any]


def _fetch_file_or_url(filename_or_url):
    """Fetch source data as Excel file"""
    logging.info("Fetching " + filename_or_url)

    # Try to read as local file if url doesn't start with http
    if not filename_or_url.lower().startswith("http"):
        with open(filename_or_url, "rb") as f:
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


def _excel_bytes_to_df(byts):
    """Convert Excel file to dataframe"""
    df = pd.read_excel(
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

def _calc_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add extra calculated columns to source data in-place"""
    df = df.copy()
    # Month (eg. 2022-01) and quarter (eg. 2020-Q01)
    df["month"] = df.date.dt.to_period("M").dt.strftime("%Y-%m")
    df["quarter"] = df.date.dt.to_period("Q").dt.strftime("%Y Q%q")
    df["posted_month"] = df.posted_date.dt.to_period("M").dt.strftime("%Y-%m")
    df["posted_quarter"] = df.posted_date.dt.to_period("Q").dt.strftime("%Y Q%q")
    # Covered by medicaid?
    r_medicaid = re.compile(r"medicaid", re.IGNORECASE)
    df["medicaid"] = df.insurance.apply(lambda x: bool(r_medicaid.match(x)))
    # Inpatient?
    r_inpt = re.compile(f"^{'|'.join(INPT_LOCATIONS)}$", re.IGNORECASE)
    df["inpatient"] = df.location.apply(lambda x: bool(r_inpt.match(x)))
    return df


def _split_by(df: pd.DataFrame, column: str) -> dict[str, pd.DataFrame]:
    """
    Split a dataframe into one dataframe per unique value in the specified column.
    Returns a dict indexed by each unique value in the column.
    Note, the returned dataframes are each views on a copy of the original dataframe.
    """
    # # Return of sorted copy of dataframe
    # df = df.sort_values(by=column, axis=0)

    # # Set the index to be the column, and don't delete the column
    # df.set_index(keys=[column], drop=False, inplace=True)

    # Create views for each unique column value
    uniq = df[column].unique().tolist()
    views = {}
    for v in uniq:
        views[v] = df.loc[df[column] == v]

    return views

def _calc_partitions(df):
    """Partition data into sets meaningful to a user and used for calculating statistics later"""
    partitions = {}

    # Office encounters - only keep rows that match one of these CPT codes
    r_wcc = re.compile("993[89][1-5]")
    r_sick = re.compile(f"992[01][1-5]|9949[56]|{RE_PROCEDURE_CODES}")
    df_outpt_all = df.loc[~df.inpatient]
    df_outpt_encs = df.loc[
        df.cpt.apply(lambda cpt: bool(r_wcc.match(cpt) or r_sick.match(cpt)))
    ]
    partitions["outpt_all"] = df_outpt_all
    partitions["outpt_encs"] = df_outpt_encs
    partitions["outpt_not_encs"] = df_outpt_all.loc[~df_outpt_all.index.isin(df_outpt_encs.index)]
    partitions["wcc_encs"] = df.loc[df.cpt.apply(lambda cpt: bool(r_wcc.match(cpt)))]
    partitions["sick_encs"] = df.loc[
        (~df.inpatient) & df.cpt.apply(lambda cpt: bool(r_sick.match(cpt)))
    ]
    partitions["outpt_medicaid_encs"] = df_outpt_encs.loc[df_outpt_encs.medicaid]

    # Aggregate wRVUs for non-encounter charges by CPT code. We use groupby().agg() to 
    # sum and count wrvu column. Retain cpt and desc by using ["cpt", "desc"] as the groupby key.
    groupby_cpt = partitions["outpt_not_encs"].groupby(["cpt", "desc"], as_index=False)
    outpt_non_enc_wrvus = groupby_cpt["wrvu"].agg(["sum", "count"]).reset_index()
    outpt_non_enc_wrvus.columns = ["CPT", "Description", "wRVUs", "n"]
    outpt_non_enc_wrvus = outpt_non_enc_wrvus[outpt_non_enc_wrvus.wRVUs > 0]
    outpt_non_enc_wrvus.sort_values('wRVUs', ascending=False, inplace=True)
    outpt_non_enc_wrvus.Description = outpt_non_enc_wrvus.Description.apply(lambda x: x[:42] + "..." if len(x) > 45 else x)
    partitions["outpt_non_enc_wrvus"] = outpt_non_enc_wrvus

    # Hospital charges - filter by service location and CPT codes
    inpt_codes = "9946[023]|9923[89]"  # newborn attendance, resusc, admit, progress, d/c, same day
    inpt_codes += "|992[23][1-3]"  # inpatient admit, progress
    inpt_codes += "|9947[7-9]|99480"  # intensive care
    inpt_codes += "|99291"  # transfer or critical care (not additional time code 99292)
    inpt_codes += "|9925[3-5]"  # inpatient consult
    inpt_codes += "|9921[89]|9922[1-6]|9923[1-9]"  # peds admit, progress, d/c
    r_inpt = re.compile(inpt_codes)
    df_inpt_encs = df.loc[df.inpatient & df.cpt.apply(lambda cpt: bool(r_inpt.match(cpt)))]
    partitions["inpt_all"] = df.loc[df.inpatient]
    partitions["inpt_encs"] = df_inpt_encs

    df_all_encs = pd.concat([df_outpt_encs, df_inpt_encs])
    partitions["all_encs"] = df_all_encs
    return partitions


def _calc_stats(df, partitions):
    """Calculate basic statistics from pre-partitioned list of charges"""
    stats = {}

    # Global stats
    stats["start_date"] = df.date.min().date()
    stats["end_date"] = df.date.max().date()
    stats["ttl_wrvu"] = df.wrvu.sum()

    # group rows by date and MRN since we can only see each pt once per day, and count number of rows
    stats["ttl_encs"] = len(partitions["all_encs"].groupby(["date", "mrn"]))
    stats["wrvu_per_encs"] = stats["ttl_wrvu"] / stats["ttl_encs"] if stats["ttl_encs"] > 0 else 0

    # Count of various outpt codes: 99211-99215, TCM, and procedure codes
    cptstr = df.cpt.str
    stats["ttl_lvl1"] = len(df[cptstr.match("992[01]1")])
    stats["ttl_lvl2"] = len(df[cptstr.match("992[01]2")])
    stats["ttl_lvl3"] = len(df[cptstr.match("992[01]3")])
    stats["ttl_lvl4"] = len(df[cptstr.match("992[01]4")])
    stats["ttl_lvl5"] = len(df[cptstr.match("992[01]5")])
    stats["ttl_tcm"] = len(df[cptstr.match("9949[56]")])
    stats["ttl_procedures"] = len(df[cptstr.match(RE_PROCEDURE_CODES)])
    stats["ttl_sick"] = len(partitions["sick_encs"])
    stats["ttl_sick_wrvu"] = partitions["sick_encs"].wrvu.sum()

    # Counts of WCCs
    stats["ttl_wccinfant"] = len(df[cptstr.match("993[89]1")])
    stats["ttl_wcc1to4"] = len(df[cptstr.match("993[89]2")])
    stats["ttl_wcc5to11"] = len(df[cptstr.match("993[89]3")])
    stats["ttl_wcc12to17"] = len(df[cptstr.match("993[89]4")])
    stats["ttl_wccadult"] = len(df[cptstr.match("993[89]5")])
    stats["ttl_wcc"] = (
        stats["ttl_wccinfant"]
        + stats["ttl_wcc1to4"]
        + stats["ttl_wcc5to11"]
        + stats["ttl_wcc12to17"]
        + stats["ttl_wccadult"]
    )
    stats["ttl_wcc_wrvu"] = partitions["wcc_encs"].wrvu.sum()

    # Outpatient stats
    stats["outpt_num_days"] = len(partitions["outpt_encs"].date.unique())
    stats["outpt_num_pts"] = len(partitions["outpt_encs"].groupby(["date", "mrn"]))
    stats["outpt_ttl_encs"] = len(partitions["outpt_encs"])
    stats["outpt_ttl_wrvu"] = partitions["outpt_encs"].wrvu.sum()
    stats["outpt_avg_wrvu_per_pt"] = stats["outpt_ttl_wrvu"] / stats["outpt_num_pts"] if stats["outpt_num_pts"] > 0 else 0
    stats["outpt_num_pts_per_day"] = stats["outpt_num_pts"] / stats["outpt_num_days"] if stats["outpt_num_days"] > 0 else 0
    stats["outpt_wrvu_per_day"] = stats["outpt_ttl_wrvu"] / stats["outpt_num_days"] if stats["outpt_num_days"] > 0 else 0
    stats["outpt_medicaid_wrvu"] = partitions["outpt_medicaid_encs"].wrvu.sum()
    stats["outpt_medicaid_pts"] = len(
        partitions["outpt_medicaid_encs"].groupby(["date", "mrn"])
    )
    stats["outpt_medicaid_wrvu_per_pt"] = (
        stats["outpt_medicaid_wrvu"] / stats["outpt_medicaid_pts"] if stats["outpt_medicaid_pts"] > 0 else 0
    )

    # Inpatient stats
    stats["inpt_num_pts"] = len(partitions["inpt_encs"].groupby(["date", "mrn"]))
    stats["inpt_ttl_wrvu"] = partitions["inpt_all"].wrvu.sum()

    return stats


# Use allow_output_mutation to avoid hashing return value to improve performance
@st.cache(show_spinner=False, allow_output_mutation=True)
def initialize(filename_or_urls: list[str]) -> RvuData:
    """Main entry point: retrieve file, src, and parse into DataFrame"""
    if filename_or_urls is None:
        return None

    # Fetch all files
    df = pd.DataFrame()
    for f in filename_or_urls:
        # Read source Excel data and append into DataFrame
        byts = _fetch_file_or_url(f)
        df = pd.concat([df, _excel_bytes_to_df(byts)])

    # Add calculated columns like month/quarter, medicaid, and inpatient
    df = _calc_columns(df)
    
    # Split into datasets for each provider
    by_provider = _split_by(df, "provider")

    # Return data
    return RvuData(
        df=df,
        start_date=df.posted_date.min(),
        end_date=df.posted_date.max(),
        by_provider=by_provider,
    )


def process(
    rvudata: RvuData, provider: str, start_date: dt.date, end_date: dt.date
) -> FilteredRvuData:
    """Process data that was returned by fetch(...) in partitions and calculate stats"""
    # Get master data set for this provider. Param, provider, is the short name
    # that is selected by the user. Use dict to translate to actual name in data.
    name = ALIAS_TO_NAME.get(provider)
    if name is None or start_date is None:
        return None

    df = rvudata.by_provider.get(name)
    if df is None:
        return None

    # Filter data by visit date with given start and end dates
    if start_date:
        df = df[df["date"].dt.date >= start_date]
    if end_date:
        df = df[df["date"].dt.date < (end_date + pd.Timedelta(days=1))]

    # Parition data for viewing and calculate stats
    partitions = _calc_partitions(df)
    stats = _calc_stats(df, partitions)

    return FilteredRvuData(
        provider=provider,
        start_date=start_date,
        end_date=end_date,
        all=rvudata,
        df=df,
        partitions=partitions,
        stats=stats,
    )
