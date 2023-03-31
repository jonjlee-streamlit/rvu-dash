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

            # Force data.initialize() to reread data from disk on next run
            st.cache_data.clear()
        return st.stop()

    # Fetch source data
    with st.spinner("Initializing..."):
        rvudata = data.initialize(data_files.get())
    
    # If no data available, display message and stop
    if rvudata is None:
        st.write("No data available. Contact administrator for details.")
        return st.stop()

    # Add sidebar widgets and get dashboard configuration
    (
        provider,
        start_date,
        end_date,
        compare_start_date,
        compare_end_date,
        visit_log_file
    ) = ui.render_sidebar(rvudata.start_date, rvudata.end_date)

    # Filter data and calculate stats
    filtered = data.process(rvudata, provider, start_date, end_date)
    compare = (
        data.process(rvudata, provider, compare_start_date, compare_end_date)
        if compare_start_date
        else None
    )

    # Validate visit log
    visit_data = None
    if visit_log_file:
        visit_data = data.validate_visits(filtered, visit_log_file.getvalue())

    # Show main display
    ui.render_main(filtered, compare, visit_data)

st.set_page_config(page_title='RVU Dashboard', layout="wide")
run()
