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
    date_range = config_ct.selectbox("Dates:", ["Specific dates", "This year", "Last year", "This quarter", "Last quarter", "This month", "Last month", "Last 12 months", "Last 4 completed quarters", "All dates"], index=1)
    if date_range == "Specific dates":
        specific_dates = config_ct.date_input("Date range:", value=(data_start_date, date.today()))
        if len(specific_dates) > 1:
            # Wait until both start and end dates selected to set date range
            start_date, end_date = specific_dates
    elif date_range == "All dates":
        start_date, end_date = data_start_date, data_end_date
    else:
        start_date, end_date = dates.get_dates(date_range)

    # Option to compare to another date range
    compare_ct = config_ct.expander("Comparison Data")
    compare = compare_ct.checkbox("Enable comparison display")
    compare_date_range = compare_ct.selectbox("Dates:", ["Specific dates", "Same days 1 month ago", "Same days 1 year ago", "This year", "Last year", "This quarter", "Last quarter", "This month", "Last month", "Last 12 months", "Last 4 completed quarters", "All dates"], index=2)
    if compare_date_range == "Specific dates":
        compare_dates = compare_ct.date_input("Date range:", key="compare_dates", value=(data_start_date, date.today()))
        if len(compare_dates) > 1:
            compare_start_date, compare_end_date = compare_dates
    elif compare_date_range == "All dates":
        compare_start_date, compare_end_date = data_start_date, data_end_date
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

    # Option to upload and validate a visit log against the RVU data
    visitlog = None
    qps = st.experimental_get_query_params()
    if qps.get("visitlog") == ["1"]:
        visitlog_ct = config_ct.expander("Visits Log")
        visitlog = visitlog_ct.file_uploader("Upload a log file to validate")

    return (provider, start_date, end_date, compare_start_date, compare_end_date, visitlog)

def render_validate_visit(visit_data: data.VisitLogData):
    """Show the Visit Log section"""
    st.header("Visit Log")

    # First print visits where there was a difference between the visits log and posted charges
    if visit_data.diff is not None and len(visit_data.diff) > 0:
        diff = visit_data.diff.copy()
        diff.columns = ["Date", "MRN", "E&M Code in Log"]
        styled = diff.style.format({'Date': lambda x: x.strftime('%m/%d/%Y')})
        st.write("Differences between visits log and posted charges:")
        st.write(styled)
    else:
        st.write("All logged visits match posted charges.")

    # Show matching entries between visits log and posted charges
    with st.expander("Show matching entries"):
        styled = visit_data.validated.style.format({'date': lambda x: x.strftime('%m/%d/%Y'), 'posted_date': lambda x: x.strftime('%m/%d/%Y')})
        st.write(visit_data.validated)

def render_dataset(data: data.FilteredRvuData, dataset_ct: st.container):
    """Show the named source dataset in the provided container"""
    if data is None:
        return

    df, partitions = data.df, data.partitions
    display_dfs = {
        'None': None,
        'All Data (including shots, etc)': df,
        'All Visits (Inpatient + Outpatient)': partitions['all_encs'],
        'Inpatient - All': partitions['inpt_all'],
        'Outpatient - All': partitions['outpt_all'],
        'Outpatient - Visits': partitions['outpt_encs'],
        'Outpatient - Well Only': partitions['wcc_encs'],
        'Outpatient - Sick Only': partitions['sick_encs'],
        'Outpatient - Other Charges': partitions['outpt_not_encs'],
    }
    dataset_name = st.selectbox("Show Data Set:", display_dfs.keys())
    display_df = display_dfs.get(dataset_name)

    # Filters for other partitions not used elsewhere
    if dataset_name == 'Clinic - 99211 and 99212':
        display_df = df[df.cpt.str.match('992[01][12]')]
    elif dataset_name == 'Clinic - 99213':
        display_df = df[df.cpt.str.match('992[01]3')]
    elif dataset_name == 'Clinic - 99214 and above':
        display_df = df[df.cpt.str.match('992[01][45]|9949[56]')]

    if not display_df is None:
        with st.spinner():
            fig.st_aggrid(display_df)

def render_main(data: data.FilteredRvuData, compare: data.FilteredRvuData, visit_data) -> None:
    """Builds the main panel using given data of type data.FilteredRvuData"""
    if data is None:
        st.markdown("<h5 style='color:#6e6e6e; padding-top:65px;'>Select a provider and date range</h5>", unsafe_allow_html=True)
        return

    df, partitions, stats, = data.df, data.partitions, data.stats
    cmp_df, cmp_partitions, cmp_stats = (compare.df, compare.partitions, compare.stats) if compare is not None else (None, None, None)

    # Is there a visit log to validate, or just standard RVU dashboard mode?
    if visit_data is None:
        # Summary stats including overall # patients and wRVUs
        st.header("Summary")
        if compare is None:
            fig.st_summary(stats, data.start_date, data.end_date, st, columns=True)
        else:
            # Write metrics in side-by-side vertical columns
            colL, colR = st.columns(2)
            fig.st_summary(stats, data.start_date, data.end_date, colL, columns=False)
            fig.st_summary(cmp_stats, compare.start_date, compare.end_date, colR, columns=False)

        # Summary graphs
        st.markdown('<p style="margin-top:0px; margin-bottom:-15px; text-align:center; color:#A9A9A9">RVU graphs do not include charges posted outside of dates, so totals may not match number above.</p>', unsafe_allow_html=True)
        if compare is None:
            enc_ct, rvu_ct = st.columns(2)
            quarter_ct = st.expander("By Quarter")
            quarter_enc_ct, quarter_rvu_ct = quarter_ct.columns(2)
            daily_ct = st.expander("By Day")
            daily_enc_ct, daily_rvu_ct = daily_ct.columns(2)
            fig.st_enc_by_month_fig(partitions, enc_ct)
            fig.st_rvu_by_month_fig(df, data.end_date, rvu_ct)
            fig.st_enc_by_quarter_fig(partitions, quarter_enc_ct)
            fig.st_rvu_by_quarter_fig(df, data.end_date, quarter_rvu_ct)
            fig.st_enc_by_day_fig(partitions, daily_enc_ct)
            fig.st_rvu_by_day_fig(df, daily_rvu_ct)
            daily_ct.markdown('<p style="margin-top:-15px; margin-bottom:10px; text-align:center; color:#A9A9A9">To zoom in, click on a graph and drag horizontally</p>', unsafe_allow_html=True)
        else:
            main_ct = st.container()
            main_colL, main_colR = main_ct.columns(2)
            quarter_ct = st.expander("By Quarter")
            quarter_colL, quarter_colR = quarter_ct.columns(2)
            daily_ct = st.expander("By Day")
            daily_colL, daily_colR = daily_ct.columns(2)
            fig.st_enc_by_month_fig(partitions, main_colL)
            fig.st_rvu_by_month_fig(df, data.end_date, main_colL)
            fig.st_enc_by_quarter_fig(partitions, quarter_colL)
            fig.st_rvu_by_quarter_fig(df, data.end_date, quarter_colL)
            fig.st_enc_by_day_fig(partitions, daily_colL)
            fig.st_rvu_by_day_fig(df, daily_colL)

            fig.st_enc_by_month_fig(cmp_partitions, main_colR)
            fig.st_rvu_by_month_fig(cmp_df, compare.end_date, main_colR)
            fig.st_enc_by_quarter_fig(cmp_partitions, quarter_colR)
            fig.st_rvu_by_quarter_fig(cmp_df, compare.end_date, quarter_colR)
            fig.st_enc_by_day_fig(cmp_partitions, daily_colR)
            fig.st_rvu_by_day_fig(cmp_df, daily_colR)

            daily_ct.markdown('<p style="margin-top:-15px; margin-bottom:10px; text-align:center; color:#A9A9A9">To zoom in, click on a graph and drag horizontally</p>', unsafe_allow_html=True)

        # Outpatient Summary
        st.header("Outpatient")
        if compare is None:
            colL, colR = st.columns(2)
            fig.st_sick_visits_fig(stats, colL)
            fig.st_wcc_visits_fig(stats, colR)
            fig.st_sick_vs_well_fig(stats, colL)
            fig.st_non_encs_fig(partitions, colR)
        else:
            colL, colR = st.columns(2)
            fig.st_sick_visits_fig(stats, colL)
            fig.st_wcc_visits_fig(stats, colL)
            fig.st_sick_vs_well_fig(stats, colL)
            fig.st_non_encs_fig(partitions, colL)
            fig.st_sick_visits_fig(cmp_stats, colR)
            fig.st_wcc_visits_fig(cmp_stats, colR)
            fig.st_sick_vs_well_fig(cmp_stats, colR)
            fig.st_non_encs_fig(cmp_partitions, colR)

        # Inpatient Summary
        st.header("Inpatient")
        if compare is None:
            inpt_enc_ct = st.empty()
            colL, colR = st.columns(2)
            fig.st_inpt_encs_fig(partitions, inpt_enc_ct)
            fig.st_inpt_vs_outpt_encs_fig(stats, colL)
            fig.st_inpt_vs_outpt_rvu_fig(stats, colR)
        else:
            colL, colR = st.columns(2)
            fig.st_inpt_vs_outpt_encs_fig(stats, colL)
            fig.st_inpt_vs_outpt_rvu_fig(stats, colL)
            fig.st_inpt_vs_outpt_encs_fig(cmp_stats, colR)
            fig.st_inpt_vs_outpt_rvu_fig(cmp_stats, colR)
    else:
        # In visit log validation mode, only validation and source data sections are shown
        render_validate_visit(visit_data)

    # Source data
    st.header("Source Data")
    dataset_ct = st.empty()
    render_dataset(data, dataset_ct)

