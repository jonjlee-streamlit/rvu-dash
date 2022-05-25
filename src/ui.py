import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from . import auth, data, fig


def config_from_sidebar(data_start_date: date, data_end_date: date) -> tuple:
    """Render widgets on sidebar for configuring dashboard"""

    start_date, end_date, compare_start_date, compare_end_date = None, None, None, None

    st.sidebar.title("RVU Dashboard")

    # Filter options by provider and dates
    st.sidebar.subheader("Select Provider and Dates:")
    provider = st.sidebar.selectbox(
        "Provider:",
        ["Select a Provider", "Gordon", "Katie", "Lee", "Mike", "Shields"],
    )
    date_col1, date_col2 = st.sidebar.columns(2)
    start_date = date_col1.date_input("Start Date:", value=data_start_date)
    end_date = date_col2.date_input("End Date:", value=date.today())

    # Option to compare to another date range
    compare = st.sidebar.checkbox("Compare to different date range")
    if compare:
        st.sidebar.subheader("Compare To:")
        date_col1, date_col2 = st.sidebar.columns(2)
        compare_start_date = date_col1.date_input(
            "Start Date:", key="compare_start", value=data_start_date
        )
        compare_end_date = date_col2.date_input(
            "End Date:", key="compare_end", value=date.today()
        )

    return (provider, start_date, end_date, compare_start_date, compare_end_date)


def render_main(data: data.FilteredRvuData, compare: data.FilteredRvuData) -> None:
    """Builds the main panel using given data of type data.FilteredRvuData"""
    if data is None:
        st.markdown("<h5 style='color:#6e6e6e; padding-top:20px;'>Select a provider to get started</h5>", unsafe_allow_html=True)
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

def render() -> None:
    """Main streamlit app entry point"""
    # Authenticate user
    if not auth.authenticate():
        st.stop()

    # Fetch source data
    with st.spinner("Initializing..."):
        rvudata = data.initialize()

    # Add sidebar widgets and get dashboard configuration
    (
        provider,
        start_date,
        end_date,
        compare_start_date,
        compare_end_date,
    ) = config_from_sidebar(rvudata.start_date, rvudata.end_date)

    # Filter data and calculate stats
    filtered = data.process(rvudata, provider, start_date, end_date)
    compare = (
        data.process(rvudata, provider, compare_start_date, compare_end_date)
        if compare_start_date
        else None
    )

    # Show main display
    render_main(filtered, compare)
