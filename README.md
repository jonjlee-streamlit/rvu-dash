# rvu-dash

Dashboard built on Streamlit to display RVU information for a provider group.

# How it works

_After several months of not working on this project, read this to get back up to speed on how the project works._

- Entry point: `/app.py`
- Data initialization:
  - `data_files.py`: provides list of data files on disk or in the `files` config parameter in streamlit secrets. Right now, we return all files in `data/*`.
  - `data.py`
    - `initialize()`
      1. Read all files given by `data_files.get()`, pass to `data_parser.get_df()` to convert to DataFrame of raw, typed data. 
      1. Add additional calculated columns, like month/quarter. 
      1. Create a map from provider alias to all transactions for that provider.
      1. The returned DataFrame has columns defined by `data_parser.COLUMN_NAMES`.
      1. Returns an `RvuData` object, which simply holds the raw data, date range found in data, and the map from provider => provider's transactions.
  - `data_parser.py`
    - `get_df()`
      - Detects the file type and returns a DataFrame with properly typed columns and the raw data from the file.
      - Currently supports .xls from Greenway and .txt files printed from Epic. 
      - Both are generated by custom reports that output data with the columns defined in `data_parser.COLUMN_NAMES`.
- Process data:
  - `data.py`
    - `process()`
      1. Receives an `RvuData` object containing raw typed DataFrame from `initialize()`
      1. Returns a `FilteredRvuData` object with:
          - `all`: reference to raw data from `RvuData`
          - `df`: DataFrame with transactions for the specific provider and date range
          - `partitions`: various views of data, such as all outpatient encounters, sick encounters, etc
          - `stats`: calculated scalar values representing stats about the filtered data in `df`, eg total encounters, num well visits, etc.
- Render:
  - `ui.render_main()`: layout of various graphs
  - `fig.py`: actual graph definitions. 


# Dev setup

- Codespaces container
  - Configured through `.devcontainer/devcontainer.json` *(generated by VSCode Codespaces: Add Dev Container Config Files... for python 3.10)*
  - As of 3/2023, per [Streamlit Cloud docs](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app), the Python 3.10 is the latest version supported
- Python and virtual environment
  - Python version specified in Codespaces container (see above)
  - Package management via [pipenv](https://pipenv-fork.readthedocs.io/en/latest/)
  - `bin/upgrade.sh`: upgrade pipenv, pip, and dependencies in Pipfile.
    - All dependencies in `Pipfile` are set to `= "*"`, so updating dependencies will pull in latest major/minor versions, including breaking changes.
  - `pipenv shell` to activate virtual env before doing work  
  - Pylance linter
    - Missing imports warnings: `Preferences: Open Workspace Settings > Extensions > Pylance > Python > Analysis: Extra Paths`. Add `/home/vscode/.local/share/virtualenvs/<...>/lib/python3.10/site-packages`. Replace `<...>` with actual path. This creates `.vscode/settings.json`.
- Configuration
  - Password: create `.streamlit/secrets.toml`:
  ```
  password = "p"
  ```
- Codespaces
  - `bin/start.sh`: start `streamlit` server inside pipenv. Use if starting in terminal. [Disables CORS, required in codespace](https://github.com/orgs/community/discussions/18038). The interactive commands are:
    ```
    pipenv shell
    streamlit run app.py --server.enableCORS false --server enableXsrfProtection false
    ```  
- VSCode
  - Update Pylance Extra Paths setting as above
  - Command `Python: Select Interpreter > select virtual env from pipenv`
  - Command `Debug: Add Configuration... > Python > Module > streamlit`. Update config in `.vscode/launch.json` to:
    ```
    {
      "name": "Streamlit",
      "type": "python",
      "request": "launch",
      "module": "streamlit",
      "args": ["run", "app.py"],
      "justMyCode": true
    }
    ```
  - In Codespaces, also add args to disable CORS protection (see above)
  - Now F5 should start streamlit to debug ([reference](https://medium.com/codefile/how-to-run-your-streamlit-apps-in-vscode-3417da669fc))
- Deploy to Streamlit Cloud
  - Push to repo will automatically redeploy to https://rvu-dash.streamlit.app/
  - Manage app, including secrets, at https://share.streamlit.io/