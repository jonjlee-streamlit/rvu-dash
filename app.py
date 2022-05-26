import streamlit as st
from src import auth, data_files, data, ui

def run():
    """Main streamlit app entry point"""
    # Authenticate user
    if not auth.authenticate():
        return st.stop()

    # Show update data screen
    qps = st.experimental_get_query_params()
    if qps.get("update") == ["1"]:
        # Allow user to upload new data files
        files, remove_existing = ui.render_upload(data_files.get_local())
        if files:
            # Write new files to data dir and list contents
            data_files.update_local(files, remove_existing)
            st.success("Data files updated.")
            st.write("Data files:")
            st.write(data_files.get_local())
        return st.stop()

    # Fetch source data
    with st.spinner("Initializing..."):
        rvudata = data.initialize(data_files.get())

    # Add sidebar widgets and get dashboard configuration
    (
        provider,
        start_date,
        end_date,
        compare_start_date,
        compare_end_date,
    ) = ui.render_sidebar(rvudata.start_date, rvudata.end_date)

    # Filter data and calculate stats
    filtered = data.process(rvudata, provider, start_date, end_date)
    compare = (
        data.process(rvudata, provider, compare_start_date, compare_end_date)
        if compare_start_date
        else None
    )

    # Show main display
    ui.render_main(filtered, compare)

st.set_page_config(layout="wide")
run()
