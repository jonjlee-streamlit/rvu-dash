import streamlit as st
import pandas as pd
import plotly.express as px
import datetime as dt
from . import auth, data, fig

def render_upload(cur_files=None):
    """Provide a way to upload updated data file"""
    st.header("Updated data files")
    if cur_files:
        st.write("Current data files:")
        st.write(cur_files)
    remove_existing = st.checkbox("Remove existing files after upload")
    files = st.file_uploader("Select files to upload", accept_multiple_files=True)
    return files, remove_existing

def render_sidebar(data_start_date: dt.date, data_end_date: dt.date) -> tuple:
    """Render widgets on sidebar for configuring dashboard"""

    start_date, end_date, compare_start_date, compare_end_date = None, None, None, None

    st.sidebar.title("RVU Dashboard")
    config_ct = st.sidebar

    # Filter options by provider and dates
    provider = config_ct.selectbox(
        "Provider:",
        ["Select a Provider", "Gordon", "Katie", "Lee", "Mike", "Shields"],
    )
    date_range = config_ct.selectbox("Dates:", ["This month", "Last month", "This year", "Last year", "This quarter", "Last quarter", "Specific dates"])
    if date_range == "This month":
        end_date = dt.date.today()
        start_date = end_date.replace(day=1)
    elif date_range == "Last month":
        this_month = dt.date.today().replace(day=1)
        end_date = this_month - dt.timedelta(days=1) # one day prior to first day of this month
        start_date = end_date.replace(day=1)
    elif date_range == "This year":
        end_date = dt.date.today()
        start_date = end_date.replace(day=1, month=1)
    elif date_range == "Last year":
        this_year = dt.date.today().replace(day=1, month=1)
        end_date = this_year - dt.timedelta(days=1) # one day prior to Jan 1
        start_date = end_date.replace(day=1, month=1)
    elif date_range == "Specific dates":
        dates = config_ct.date_input("Select dates:", value=(data_start_date, dt.date.today()))
        if len(dates) > 1:
            # Wait until both start and end dates selected to set date range
            start_date, end_date = dates
    else:
        start_date, end_date = None, None

    # Option to compare to another date range
    config_ct.subheader("Compare To:")
    compare_ct = config_ct.expander("Show options")
    compare = compare_ct.checkbox("Enable comparison")
    compare_date_range = compare_ct.selectbox("Date range:", ["Same days last month", "Same days last year", "This month", "Last month", "2 months ago", "This year", "Last year", "This quarter", "Last quarter", "Specific dates"])
    if date_range == "Specific dates":
        compare_start_date, compare_end_date = compare_ct.date_input("Date range:", key="compare_dates", value=(data_start_date, dt.date.today()))
    if not compare:
        # Do not perform comparison if enable box is unchecked, so clear dates
        compare_start_date, compare_end_date = None, None

    return (provider, start_date, end_date, compare_start_date, compare_end_date)


def render_main(data: data.FilteredRvuData, compare: data.FilteredRvuData) -> None:
    """Builds the main panel using given data of type data.FilteredRvuData"""
    if data is None:
        st.markdown("<h5 style='color:#6e6e6e; padding-top:65px;'>Select a provider and date range</h5>", unsafe_allow_html=True)
        return

    df, partitions, stats = data.df, data.partitions, data.stats
    cmp_df, cmp_partitions, cmp_stats = (compare.df, compare.partitions, compare.stats) if compare is not None else (None, None, None)

    # Summary stats including overall # patients and wRVUs
    st.header("Summary")
    if compare is None:
        dates_ct = st.empty()
        ct1, ct2, ct3 = st.columns(3)
        fig.st_summary(stats, dates_ct, ct1, ct2, ct3)
    else:
        # Write metrics in side-by-side vertical columns
        colL, colR = st.columns(2)
        fig.st_summary(stats, colL, colL, colL, colL)
        fig.st_summary(cmp_stats, colR, colR, colR, colR)

    # Summary graphs
    if compare is None:
        main_ct = st.container()
        quarter_ct = st.expander("By Quarter")
        daily_ct = st.expander("By Day")
        fig.st_summary_figs(df, partitions, main_ct, quarter_ct, daily_ct)
    else:
        main_ct = st.container()
        main_colL, main_colR = main_ct.columns(2)
        quarter_ct = st.expander("By Quarter")
        quarter_colL, quarter_colR = quarter_ct.columns(2)
        daily_ct = st.expander("By Day")
        daily_colL, daily_colR = daily_ct.columns(2)
        fig.st_summary_figs(df, partitions, main_colL, quarter_colL, daily_colL)
        fig.st_summary_figs(cmp_df, cmp_partitions, main_colR, quarter_colR, daily_colR)