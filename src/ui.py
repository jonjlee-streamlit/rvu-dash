import streamlit as st
import pandas as pd
from datetime import date
from . import data
from .auth import authenticate


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
        st.write(
            f"{stats['start_date'].strftime('%a %b %d, %Y')} to {stats['end_date'].strftime('%a %b %d, %Y')}",
        )
        col1, col2, col3 = st.columns(3)
        col1.metric("Encounters", stats["ttl_encs"])
        col2.metric("Total wRVU", round(stats["ttl_wrvu"]))
        col3.metric("wRVU / encounter", round(stats["wrvu_per_encs"], 2))
    else:
        colL, colR = st.columns(2)
        colL.write(
            f"{stats['start_date'].strftime('%a %b %d, %Y')} to {stats['end_date'].strftime('%a %b %d, %Y')}",
        )
        colR.write(
            f"{cmp_stats['start_date'].strftime('%a %b %d, %Y')} to {cmp_stats['end_date'].strftime('%a %b %d, %Y')}",
        )
        colL.metric("Encounters", stats["ttl_encs"])
        colL.metric("Total wRVU", round(stats["ttl_wrvu"]))
        colL.metric("wRVU / encounter", round(stats["wrvu_per_encs"], 2))

        colR.metric("Encounters", cmp_stats["ttl_encs"])
        colR.metric("Total wRVU", round(cmp_stats["ttl_wrvu"]))
        colR.metric("wRVU / encounter", round(cmp_stats["wrvu_per_encs"], 2))

    # Graphs of number of visits
    df_encounters_by_month = partitions["all_encs"].copy()
    df_encounters_by_month["Month"] = df_encounters_by_month["date"].apply(
        lambda x: x.date().strftime("%Y-%m")
    )
    encounters_by_month_src = (
        df_encounters_by_month.groupby("Month").mrn.count().reset_index()
    )
    encounters_by_month_src.columns = ["Month", "Encounters"]
    st.bar_chart(encounters_by_month_src)
    # encounters_by_month_fig = px.bar(encounters_by_month_src, x='Month', y='Encounters', text='Encounters', text_auto='i')


def render() -> None:
    """Main streamlit app entry point"""

    # Authenticate user
    if not authenticate():
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
