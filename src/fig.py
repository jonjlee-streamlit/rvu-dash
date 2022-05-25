import streamlit as st
import pandas as pd

def st_summary(stats, dates_ct, ct1, ct2, ct3):
    """Render summary stats"""
    dates_ct.write(
        f"{stats['start_date'].strftime('%a %b %d, %Y')} to {stats['end_date'].strftime('%a %b %d, %Y')}",
    )
    ct1.metric("Encounters", stats["ttl_encs"])
    ct2.metric("Total wRVU", round(stats["ttl_wrvu"]))
    ct3.metric("wRVU / encounter", round(stats["wrvu_per_encs"], 2))