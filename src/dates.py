import arrow
from datetime import date

def get_dates(date_range: str) -> date:
    """Convert a human readable string to starting and ending date objects"""
    start_date, end_date = None, None
    today = arrow.now().floor("day")
    if date_range == "This month":
        end_date = today
        start_date = end_date.floor("month")
    elif date_range == "Last month":
        end_date = today.floor("month").shift(days=-1) # one day prior to first day of this month
        start_date = end_date.floor("month")
    elif date_range == "2 months ago":
        end_date = today.floor("month").shift(months=-1, days=-1)
        start_date = end_date.floor("month")
    elif date_range == "This year":
        end_date = today
        start_date = end_date.floor("year")
    elif date_range == "Last year":
        end_date = today.floor("year").shift(days=-1) # one day prior to Jan 1
        start_date = end_date.floor("year")
    elif date_range == "2 years ago":
        end_date = today.floor("year").shift(years=-1, days=-1)
        start_date = end_date.floor("year")
    elif date_range == "This quarter":
        end_date = today
        start_date = end_date.floor("quarter")
    elif date_range == "Last quarter":
        end_date = today.floor("quarter").shift(days=-1) # one day prior to first day of this quarter
        start_date = end_date.floor("quarter")
    elif date_range == "2 quarters ago":
        end_date = today.floor("quarter").shift(quarters=-1, days=-1)
        start_date = end_date.floor("quarter")
    elif date_range == "3 quarters ago":
        end_date = today.floor("quarter").shift(quarters=-2, days=-1)
        start_date = end_date.floor("quarter")
    
    if start_date and end_date:
        return start_date.date(), end_date.date()
    
    return None, None
