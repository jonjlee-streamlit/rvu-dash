import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from . import data
from .auth import authenticate

SOURCE_FILES = ["rvudata.xls"]


def config_from_sidebar():
    """Render widgets on sidebar for configuring dashboard"""

    start_date, end_date, compare_start_date, compare_end_date = None, None, None, None

    # Filter options by provider and dates
    st.sidebar.subheader("Select Provider and Dates:")
    provider = st.sidebar.selectbox(
        "Provider:", ["Gordon", "Katie", "Lee", "Mike", "Shields"]
    )
    date_col1, date_col2 = st.sidebar.columns(2)
    start_date = date_col1.date_input("Start Date:", value=date(2020, 1, 1))
    end_date = date_col2.date_input("End Date:", value=date.today())

    # Option to compare to another date range
    compare = st.sidebar.checkbox("Compare to different date range")
    if compare:
        st.sidebar.subheader("Compare To:")
        date_col1, date_col2 = st.sidebar.columns(2)
        compare_start_date = date_col1.date_input(
            "Start Date:", key="compare_start", value=date(2020, 1, 1)
        )
        compare_end_date = date_col2.date_input(
            "End Date:", key="compare_end", value=date.today()
        )

    return (provider, start_date, end_date, compare_start_date, compare_end_date)


def render():
    """Main streamlit app entry point"""

    st.title("RVU Dashboard -x ")

    # Authenticate user
    if not authenticate():
        st.stop()

    # Add sidebar widgets and get dashboard configuration
    (
        provider,
        start_date,
        end_date,
        compare_start_date,
        compare_end_date,
    ) = config_from_sidebar()

    # Fetch and process data
    rvudata = data.fetch(SOURCE_FILES)
    st.write(f"First date: {rvudata.start_date}")
    st.write(f"Last date: {rvudata.end_date}")
    st.dataframe(rvudata.df)
