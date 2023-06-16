import os

# Location of data files: rvu-dash/data/
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def get():
    """Return list of data files. Defaults to 'files' config var if set, otherwise list of local files"""
    return os.environ.get("STREAMLIT_DATA_FILES") or get_local()


def get_local():
    """Return list of local data files"""
    if not os.path.isdir(BASE_PATH):
        return []

    return [os.path.join(BASE_PATH, local) for local in os.listdir(BASE_PATH)]


def update_local(files, remove_existing):
    if files is None or len(files) == 0:
        return

    # Ensure base data directory exists
    os.makedirs(BASE_PATH, exist_ok=True)

    # Delete all files if requested
    if remove_existing:
        for local in os.listdir(BASE_PATH):
            os.remove(os.path.join(BASE_PATH, local))

    # Save new files to data dir
    for file in files:
        with open(os.path.join(BASE_PATH, file.name), "wb") as local:
            local.write(file.read())
