import streamlit as st
import pandas as pd
import plotly.express as px
import datetime as dt
import arrow
from datetime import date
from . import auth, data, fig, dates

def render_upload(cur_files: list = None):
    """Provide a way to upload updated data file"""
    st.header("Updated data files")
    if cur_files:
        st.write("Current data files:")
        st.write(cur_files)
    remove_existing = st.checkbox("Remove existing files after upload")
    files = st.file_uploader("Select files to upload", accept_multiple_files=True)
    return files, remove_existing

def render_sidebar(data_start_date: date, data_end_date: date) -> tuple[str, date, date, date, date]:
    """Render widgets on sidebar for configuring dashboard"""

    start_date, end_date, compare_start_date, compare_end_date = None, None, None, None

    st.sidebar.title("RVU Dashboard")
    config_ct = st.sidebar

    # Filter options for providers
    provider = config_ct.selectbox(
        "Provider:",
        ["Select a Provider", "Gordon", "Katie", "Lee", "Mike", "Shields"],
    )

    # Preset date filters
    date_range = config_ct.selectbox("Dates:", ["Specific dates below", "This year", "Last year", "This quarter", "Last quarter", "This month", "Last month"])
    if date_range == "Specific dates below":
        specific_dates = config_ct.date_input("Date range:", value=(data_start_date, date.today()))
        if len(specific_dates) > 1:
            # Wait until both start and end dates selected to set date range
            start_date, end_date = specific_dates
    else:
        start_date, end_date = dates.get_dates(date_range)

    # Option to compare to another date range
    compare_ct = config_ct.expander("Comparison Data")
    compare = compare_ct.checkbox("Show comparison display")
    compare_date_range = compare_ct.selectbox("Dates:", ["Specific dates below", "Same days 1 month ago", "Same days 1 year ago", "This year", "Last year", "This quarter", "Last quarter", "This month", "Last month"])
    if compare_date_range == "Specific dates below":
        compare_dates = compare_ct.date_input("Date range:", key="compare_dates", value=(data_start_date, date.today()))
        if len(compare_dates) > 1:
            compare_start_date, compare_end_date = compare_dates
    elif compare_date_range == "Same days 1 month ago" and start_date is not None:
        compare_start_date = arrow.get(start_date).shift(months=-1).date()
        compare_end_date = arrow.get(end_date).shift(months=-1).date()
    elif compare_date_range == "Same days 1 year ago" and start_date is not None:
        compare_start_date = arrow.get(start_date).shift(years=-1).date()
        compare_end_date = arrow.get(end_date).shift(years=-1).date()
    else:
        compare_start_date, compare_end_date = dates.get_dates(compare_date_range)
    if not compare:
        # Do not perform comparison if enable box is unchecked, so clear dates
        compare_start_date, compare_end_date = None, None

    return (provider, start_date, end_date, compare_start_date, compare_end_date)


def render_main(data: data.FilteredRvuData, compare: data.FilteredRvuData) -> None:
    """Builds the main panel using given data of type data.FilteredRvuData"""
    if data is None:
        st.markdown("<h5 style='color:#6e6e6e; padding-top:65px;'>Select a provider and date range</h5>", unsafe_allow_html=True)
        return

    df, partitions, stats, = data.df, data.partitions, data.stats
    cmp_df, cmp_partitions, cmp_stats = (compare.df, compare.partitions, compare.stats) if compare is not None else (None, None, None)

    # Summary stats including overall # patients and wRVUs
    st.header("Summary")
    if compare is None:
        dates_ct = st.empty()
        ct1, ct2, ct3 = st.columns(3)
        fig.st_summary(stats, data.start_date, data.end_date, dates_ct, ct1, ct2, ct3)
    else:
        # Write metrics in side-by-side vertical columns
        colL, colR = st.columns(2)
        fig.st_summary(stats, data.start_date, data.end_date, colL, colL, colL, colL)
        fig.st_summary(cmp_stats, compare.start_date, compare.end_date, colR, colR, colR, colR)

    # Summary graphs
    if compare is None:
        enc_ct, rvu_ct = st.columns(2)
        quarter_ct = st.expander("By Quarter")
        quarter_enc_ct, quarter_rvu_ct = quarter_ct.columns(2)
        daily_ct = st.expander("By Day")
        daily_enc_ct, daily_rvu_ct = daily_ct.columns(2)
        fig.st_summary_figs(df, partitions, enc_ct, rvu_ct, quarter_enc_ct, quarter_rvu_ct, daily_enc_ct, daily_rvu_ct)
    else:
        main_ct = st.container()
        main_colL, main_colR = main_ct.columns(2)
        quarter_ct = st.expander("By Quarter")
        quarter_colL, quarter_colR = quarter_ct.columns(2)
        daily_ct = st.expander("By Day")
        daily_colL, daily_colR = daily_ct.columns(2)
        fig.st_summary_figs(df, partitions, main_colL, main_colL, quarter_colL, quarter_colL, daily_colL, daily_colL)
        fig.st_summary_figs(cmp_df, cmp_partitions, main_colR, main_colR, quarter_colR, quarter_colR, daily_colR, daily_colR)

    # Outpatient Summary
    st.header("Outpatient")
    if compare is None:
        sick_visits_ct, sick_vs_well_ct = st.columns(2)
        fig.st_sick_visits_fig(stats, sick_visits_ct)
        fig.st_sick_vs_well_fig(stats, sick_vs_well_ct)
    else:
        colL, colR = st.columns(2)
        fig.st_sick_visits_fig(stats, colL)
        fig.st_sick_vs_well_fig(stats, colL)
        fig.st_sick_visits_fig(cmp_stats, colR)
        fig.st_sick_vs_well_fig(cmp_stats, colR)

    # Inpatient Summary
    st.header("Inpatient")
    if compare is None:
        inpt_enc_ct, inpt_rvu_ct = st.columns(2)
        fig.st_inpt_vs_outpt_encs_fig(stats, inpt_enc_ct)
        fig.st_inpt_vs_outpt_rvu_fig(stats, inpt_rvu_ct)
    else:
        colL, colR = st.columns(2)
        fig.st_inpt_vs_outpt_encs_fig(stats, colL)
        fig.st_inpt_vs_outpt_rvu_fig(stats, colL)
        fig.st_inpt_vs_outpt_encs_fig(cmp_stats, colR)
        fig.st_inpt_vs_outpt_rvu_fig(cmp_stats, colR)
