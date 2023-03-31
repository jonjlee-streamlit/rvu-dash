import io
import logging
import re
import pandas as pd

# Columns to use from Excel sheet and the corresponding column names
GW_SOURCE_COLUMNS = "B,C,D,E,G,H,I,K,N,P,R,S,T"
EPIC_COLUMN_POSITIONS = [0,12,24,50,62,62,83,164,170,178,178,187,223,264]
COLUMN_NAMES = [
    "posted_date",
    "date",
    "provider",
    "mrn",
    "visitid",
    "cpt",
    "desc",
    "units",
    "wrvu",
    "charge",
    "net",
    "insurance",
    "location",
]

def _is_gw_source(fname: str, byts: bytes) -> bool:
    # Treat all .xls Excel files as exports from Greenway
    return fname.lower().endswith('.xls')

def _is_epic_fixedwidth(fname: str, byts: bytes) -> bool:
    # Treat all .txt files as fixed width virtual prints from Epic
    return fname.lower().endswith('.txt')

def _gw_excel_to_df(byts: bytes) -> pd.DataFrame:
    """Convert Excel file to dataframe"""
    df = pd.read_excel(
        io.BytesIO(byts),
        usecols=GW_SOURCE_COLUMNS,
        names=COLUMN_NAMES,
        dtype={"cpt": str},
    )
    # Parse date columns
    df.posted_date = pd.to_datetime(df.posted_date, errors="coerce")
    df.date = pd.to_datetime(df.date, errors="coerce")
    # Filter out NaN values
    df = df[df.posted_date.notnull() & df.provider.notnull()]
    return df

def _epic_fixedwidth_to_df(byts: bytes) -> pd.DataFrame:
    # Convert bytes to string
    txt = str(byts, 'UTF-8')
    
    # Clear lines that don't start with a date (ie, either 0 or 1, which would be first digit of month)
    # then remove empty lines
    filtered = re.sub(r'^[^0-1]+.*', '', txt, flags=re.MULTILINE)
    filtered = re.sub(r'^\s*\r?\n', '', filtered, flags=re.MULTILINE)

    # Convert fixed width data to dataframe
    # Column positions are defined in the Epic Report Settings > Print Layout
    data = []
    positions = EPIC_COLUMN_POSITIONS
    for ln in filtered.splitlines():
        data.append(tuple(ln[pos:positions[i+1]].strip() for i, pos in enumerate(positions[:-1])))
    df = pd.DataFrame(data, columns=COLUMN_NAMES)

    # Set specific column types
    df.cpt = pd.Categorical(df.cpt)
    df.wrvu = pd.to_numeric(df.wrvu)
    df.units = pd.to_numeric(df.units)
    df.posted_date = pd.to_datetime(df.posted_date, errors="coerce")
    df.date = pd.to_datetime(df.date, errors="coerce")
    
    return df    

def get_df(fname: str, byts: bytes) -> pd.DataFrame:
    """Main export for module. Parses a file given its filename and contents and returns a DataFrame"""
    # Detect source file type and return appropriate parser 
    if _is_gw_source(fname, byts):
        return _gw_excel_to_df(byts)
    elif _is_epic_fixedwidth(fname, byts):
        return _epic_fixedwidth_to_df(byts)
    else:
        return None