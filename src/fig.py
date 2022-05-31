import streamlit as st
import pandas as pd
import plotly.express as px

def st_summary(stats, start_date, end_date, ct, columns=True):
    """Render summary stats"""
    ct.write(
        f"{start_date.strftime('%b %d, %Y (%a)')} to {end_date.strftime('%b %d, %Y (%a)')}",
    )
    if columns:
        ct1, ct2, ct3, ct4 = ct.columns(4)
    else:
        ct1, ct2, ct3, ct4 = ct, ct, ct, ct
    ct1.metric("Encounters", stats["ttl_encs"])
    ct2.metric("Total wRVU", round(stats["ttl_wrvu"]))
    ct3.metric("wRVU / encounter", round(stats["wrvu_per_encs"], 2))
    ct4.metric("Last Visit", stats["end_date"].strftime("%m-%d-%y"))

def st_enc_by_month_fig(partitions, ct):
    """Bar graph of number of visits"""
    src = partitions["all_encs"].groupby(["month"]).mrn.nunique().reset_index()
    src.columns = ["Month", "Encounters"]
    fig = px.bar(src, title="Encounters", x="Month", y="Encounters", text="Encounters", text_auto="i")
    fig.update_layout(title_x=0.5) # Center title
    fig.update_xaxes(tickformat="%b %Y") # Make x-axis dates show only month and year
    ct.plotly_chart(fig, use_container_width=True)

    # To create stacked bars for inpatient/outpatient, replace src with the following:
    # src = partitions["all_encs"].groupby(["month", "inpatient"]).mrn.nunique().reset_index()
    # src.columns = ["Month", "Setting", "Encounters"]
    # src["Setting"] = src["Setting"].apply(lambda x: "Inpatient" if x else "Outpatient")
    # fig = px.bar(src, title="Encounters", x="Month", y="Encounters", color="Setting", text="Encounters", text_auto="i", hover_data={"Setting": False})

def st_enc_by_quarter_fig(partitions, ct):
    src = partitions["all_encs"].groupby(["quarter"]).mrn.nunique().reset_index()
    src.columns = ["Quarter", "Encounters"]
    fig = px.bar(src, title="Encounters by Quarter", x="Quarter", y="Encounters", text="Encounters", text_auto="i")
    ct.plotly_chart(fig, use_container_width=True)

def st_enc_by_day_fig(partitions, ct):
    src = partitions["all_encs"].groupby(["date"]).mrn.nunique().reset_index()
    src.columns = ["Date", "Encounters"]
    fig = px.bar(src, title="Encounters by Day", x="Date", y="Encounters", text="Encounters", text_auto="i")
    fig.update_xaxes(tickformat="%a %m-%d-%y") # Make x-axis dates include weekday and show only date, even when zoomed in (ie. no time)
    ct.plotly_chart(fig, use_container_width=True)    

def st_rvu_by_month_fig(df, end_date, ct):
    """
    Bar graph of wRVUs. Note that for month/quarter, we are using the charge posted date like the
    clinic does, so number match and the user knows what to expect at when comparing to the production report.
    However, for wRVU/day, we showing it with the actual visit date, which is more helpful for understanding
    actual production.
    """
    # Data was filtered on visit date, not posted date. Since charges may be posted after our specified time period,
    # remove the ones out of our period to avoid confusion for the user.
    df = df[df["posted_date"].dt.date < (end_date + pd.Timedelta(days=1))]

    # Group and add wrvus by month
    src = df.groupby("posted_month").wrvu.sum().reset_index()
    src.columns = ["Month", "wRVUs"]
    fig = px.bar(src, title="wRVUs", x="Month", y="wRVUs", text="wRVUs", text_auto=".1f", hover_data={"wRVUs": ":.1f"}).update_traces(marker_color="#00ac75")
    fig.update_layout(title_x=0.5)
    fig.update_xaxes(tickformat="%b %Y")
    ct.plotly_chart(fig, use_container_width=True)    

def st_rvu_by_quarter_fig(df, end_date, ct):
    # Filter out posted charges outside of the filtered time period (see comment in st_rvu_by_month_fig())
    df = df[df["posted_date"].dt.date < (end_date + pd.Timedelta(days=1))]

    # Group and add wrvus by quarter
    src = df.groupby("posted_quarter").wrvu.sum().reset_index()
    src.columns = ["Quarter", "wRVUs"]
    fig = px.bar(src, title="wRVUs by Quarter", x="Quarter", y="wRVUs", text="wRVUs", text_auto=".1f", hover_data={"wRVUs": ":.1f"}).update_traces(marker_color="#00ac75")
    ct.plotly_chart(fig, use_container_width=True)    

def st_rvu_by_day_fig(df, ct):
    src = df.groupby("date").wrvu.sum().reset_index()
    src.columns = ["Day", "wRVUs"]
    fig = px.bar(src, title="wRVUs by Day", x="Day", y="wRVUs", text="wRVUs", text_auto=".1f", hover_data={"wRVUs": ":.1f"}).update_traces(marker_color="#00ac75")
    fig.update_xaxes(tickformat="%a %m-%d-%y") # Make x-axis dates include weekday and show only date, even when zoomed in (ie. no time)
    ct.plotly_chart(fig, use_container_width=True)    

def st_sick_visits_fig(stats, ct):
    """Breakdown of sick visit types (99213 vs 99214, etc) pie chart"""
    src = pd.DataFrame({
    "CPT": ["9920/11 ({n})".format(n=stats["ttl_lvl1"]),
            "9920/12 ({n})".format(n=stats["ttl_lvl2"]),
            "9920/13 ({n})".format(n=stats["ttl_lvl3"]),
            "9920/14 ({n})".format(n=stats["ttl_lvl4"]),
            "9920/15 or TCM ({n})".format(n=stats["ttl_lvl5"] + stats["ttl_tcm"]),
            "Procedures ({n})".format(n=stats["ttl_procedures"])],
    "n": [stats["ttl_lvl1"], 
            stats["ttl_lvl2"], 
            stats["ttl_lvl3"], 
            stats["ttl_lvl4"],
            stats["ttl_lvl5"] + stats["ttl_tcm"],
            stats["ttl_procedures"]]
    })
    fig = px.pie(src, title="Sick Visit Types", values="n", names="CPT", hole=.5)
    fig.update_traces(sort=False) 
    ct.plotly_chart(fig, use_container_width=True)

def st_sick_vs_well_fig(stats, ct):
    """Sick vs well pie chart"""
    src = pd.DataFrame({
        "Type": ["Sick/Procedure ({n} pts)".format(n=stats["sick_num_pts"]), 
                "Well ({n} pts)".format(n=stats["wcc_num_pts"])],
        "n": [stats["sick_num_pts"], 
            stats["wcc_num_pts"]]
    })
    fig = px.pie(src, title="Charge Types", values="n", names="Type", hole=.5)
    fig.update_traces(sort=False) 
    ct.plotly_chart(fig, use_container_width=True)

def st_wcc_visits_fig(stats, ct):
    """Breakdown of well visit types by age"""
    src = pd.DataFrame({
        "Type": ["Infant ({n})".format(n=stats["ttl_wccinfant"]),
                "1 to 4y ({n})".format(n=stats["ttl_wcc1to4"]),
                "5 to 11y ({n})".format(n=stats["ttl_wcc5to11"]),
                "12 to 17y ({n})".format(n=stats["ttl_wcc12to17"]),
                "18y and over ({n})".format(n=stats["ttl_wccadult"])],
        "n": [stats["ttl_wccinfant"], 
                stats["ttl_wcc1to4"], 
                stats["ttl_wcc5to11"], 
                stats["ttl_wcc12to17"],
                stats["ttl_wccadult"]]
    })
    fig = px.pie(src, title="Well Visit Types", values="n", names="Type", hole=.5)
    fig.update_traces(sort=False) 
    ct.plotly_chart(fig, use_container_width=True)

def st_non_encs_fig(partitions, ct):
    """Bar chart of non-encounter charges (e.g. shots, fluoride, etc), sorted by most total wRVUs"""
    src = partitions["outpt_non_enc_wrvus"]
    fig = px.bar(src, title="Other CPT codes", x="CPT", y="wRVUs", custom_data=["Description", "n"])
    fig.update_traces(
        hovertemplate="<br>".join([
            "%{x} (%{customdata[0]})",
            "wRVUs: %{y:.1f}",
            "n: %{customdata[1]}",
        ]),
        marker_color="#00ac75")
    fig.update_layout(hovermode="x")
    ct.plotly_chart(fig, use_container_width=True)

def st_inpt_encs_fig(partitions, ct):
    src = partitions["inpt_all"].groupby("date").mrn.nunique().reset_index()
    src.columns = ["Date", "Encounters"]
    fig = px.bar(src, title="Encounters by Day", x="Date", y="Encounters", text="Encounters", text_auto="i")
    fig.update_xaxes(tickformat="%a %m-%d-%y") # Make x-axis dates include weekday and show only date, even when zoomed in (ie. no time)
    ct.plotly_chart(fig, use_container_width=True)    

def st_inpt_vs_outpt_encs_fig(stats, ct):
    src = pd.DataFrame({
        "Type": ["Outpatient ({n} pts)".format(n=stats["outpt_num_pts"]), 
                "Inpatient ({n} pts)".format(n=stats["inpt_num_pts"])],
        "n": [stats["outpt_num_pts"], 
            stats["inpt_num_pts"]]
    })
    fig = px.pie(src, title="Encounters", values="n", names="Type", hole=.5)
    fig.update_traces(sort=False) 
    ct.plotly_chart(fig, use_container_width=True)

def st_inpt_vs_outpt_rvu_fig(stats, ct):
    src = pd.DataFrame({
    "Type": ["Outpatient ({n} wRVU)".format(n=round(stats["outpt_ttl_wrvu"], 1)), 
            "Inpatient ({n} wRVU)".format(n=round(stats["inpt_ttl_wrvu"], 1))],
    "n": [stats["outpt_ttl_wrvu"], 
          stats["inpt_ttl_wrvu"]]
    })
    fig = px.pie(src, title="wRVUs", values="n", names="Type", hole=.5)
    fig.update_traces(sort=False) 
    ct.plotly_chart(fig, use_container_width=True)
