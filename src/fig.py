import streamlit as st
import pandas as pd
import plotly.express as px

def st_summary(stats, start_date, end_date, dates_ct, ct1, ct2, ct3):
    """Render summary stats"""
    dates_ct.write(
        f"{start_date.strftime('%a %b %d, %Y')} to {end_date.strftime('%a %b %d, %Y')}",
    )
    ct1.metric("Encounters", stats["ttl_encs"])
    ct2.metric("Total wRVU", round(stats["ttl_wrvu"]))
    ct3.metric("wRVU / encounter", round(stats["wrvu_per_encs"], 2))

def st_summary_figs(df, partitions, enc_ct, rvu_ct, quarter_enc_ct, quarter_rvu_ct, daily_enc_ct, daily_rvu_ct):
    # Number of visits
    encounters_by_quarter_src = partitions["all_encs"].groupby("quarter").mrn.count().reset_index()
    encounters_by_quarter_src.columns = ["Quarter", "Encounters"]
    encounters_by_quarter_fig = px.bar(encounters_by_quarter_src, x="Quarter", y="Encounters", text="Encounters", text_auto="i")

    encounters_by_month_src = partitions["all_encs"].groupby("month").mrn.count().reset_index()
    encounters_by_month_src.columns = ["Month", "Encounters"]
    encounters_by_month_fig = px.bar(encounters_by_month_src, x="Month", y="Encounters", text="Encounters", text_auto="i")

    encounters_by_day_src = partitions["all_encs"].groupby("date").mrn.count().reset_index()
    encounters_by_day_src.columns = ["Date", "Encounters"]
    encounters_by_day_fig = px.bar(encounters_by_day_src, x="Date", y="Encounters", text="Encounters", text_auto="i")

    # wRVUs. Note that for month/quarter, we are using the charge posted date like the
    # clinic does, so number match and the user knows what to expect at when comparing to the production report.
    # However, for wRVU/day, we showing it with the actual visit date, which is more helpful for understanding
    # actual production.
    wrvu_by_month_src = df.groupby("posted_month").wrvu.sum().reset_index()
    wrvu_by_month_src.columns = ["Month", "wRVUs"]
    wrvu_by_month_fig = px.bar(wrvu_by_month_src, x="Month", y="wRVUs", text="wRVUs", text_auto=".1f", hover_data={"wRVUs": ":.1f"}).update_traces(marker_color="#2ca02c")

    wrvu_by_quarter_src = df.groupby("posted_quarter").wrvu.sum().reset_index()
    wrvu_by_quarter_src.columns = ["Quarter", "wRVUs"]
    wrvu_by_quarter_fig = px.bar(wrvu_by_quarter_src, x="Quarter", y="wRVUs", text="wRVUs", text_auto=".1f", hover_data={"wRVUs": ":.1f"}).update_traces(marker_color="#2ca02c")

    wrvu_by_day_src = df.groupby("date").wrvu.sum().reset_index()
    wrvu_by_day_src.columns = ["Day", "wRVUs"]
    wrvu_by_day_fig = px.bar(wrvu_by_day_src, x="Day", y="wRVUs", text="wRVUs", text_auto=".1f", hover_data={"wRVUs": ":.1f"}).update_traces(marker_color="#2ca02c")

    # Display charts
    enc_ct.markdown('<h4 style="text-align:center;padding-bottom:0px;">Encounters</h4>', unsafe_allow_html=True)
    enc_ct.plotly_chart(encounters_by_month_fig, use_container_width=True)
    rvu_ct.markdown('<h4 style="text-align:center;padding-bottom:0px;">wRVUs (by Month Posted)</h4>', unsafe_allow_html=True)
    rvu_ct.plotly_chart(wrvu_by_month_fig, use_container_width=True)

    quarter_enc_ct.markdown('<h4 style="text-align:center;padding-bottom:0px;">Encounters by Quarter</h4>', unsafe_allow_html=True)
    quarter_enc_ct.plotly_chart(encounters_by_quarter_fig, use_container_width=True)
    quarter_rvu_ct.markdown('<h4 style="text-align:center;padding-bottom:0px;">wRVUs by Quarter (Posted)</h4>', unsafe_allow_html=True)
    quarter_rvu_ct.plotly_chart(wrvu_by_quarter_fig, use_container_width=True)

    daily_enc_ct.markdown('<h4 style="text-align:center;padding-bottom:0px;">Encounters</h4>', unsafe_allow_html=True)
    daily_enc_ct.plotly_chart(encounters_by_day_fig, use_container_width=True)
    daily_rvu_ct.markdown('<h4 style="text-align:center;padding-bottom:0px;">wRVUs (by Visit Date)</h4>', unsafe_allow_html=True)
    daily_rvu_ct.plotly_chart(wrvu_by_day_fig, use_container_width=True)