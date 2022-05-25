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
        "Provider:", ["Gordon", "Katie", "Lee", "Mike", "Shields"]
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
    df, partitions, stats = data.df, data.partitions, data.stats
    cmp_stats = compare.stats if compare is not None else None

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

    # Graphs of number of visits
    encounters_by_quarter_src = partitions["all_encs"].groupby("quarter").mrn.count().reset_index()
    encounters_by_quarter_src.columns = ["Quarter", "Encounters"]
    encounters_by_quarter_fig = px.bar(encounters_by_quarter_src, x="Quarter", y="Encounters", text="Encounters", text_auto="i")

    encounters_by_month_src = partitions["all_encs"].groupby("month").mrn.count().reset_index()
    encounters_by_month_src.columns = ["Month", "Encounters"]
    encounters_by_month_fig = px.bar(encounters_by_month_src, x="Month", y="Encounters", text="Encounters", text_auto="i")

    encounters_by_day_src = partitions["all_encs"].groupby("date").mrn.count().reset_index()
    encounters_by_day_src.columns = ["Date", "Encounters"]
    encounters_by_day_fig = px.bar(encounters_by_day_src, x="Date", y="Encounters", text="Encounters", text_auto="i")

    st.markdown("<h4 style='text-align:center;'>Encounters By Month</h4>", unsafe_allow_html=True)
    st.plotly_chart(encounters_by_month_fig, use_container_width=True)
    ct1, ct2 = st.columns(2)
    ct1.markdown("<h4 style='text-align:center;'>By Quarter</h4>", unsafe_allow_html=True)
    ct1.plotly_chart(encounters_by_quarter_fig, use_container_width=True)
    ct2.markdown("<h4 style='text-align:center;'>By Day</h4>", unsafe_allow_html=True)
    ct2.plotly_chart(encounters_by_day_fig, use_container_width=True)


def render() -> None:
    """Main streamlit app entry point"""
    # Authenticate user
    if not auth.authenticate():
        st.stop()

    # Fetch source data
    rvudata = data.fetch()

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
