import datetime

def format_date(raw_date):
    """
    Extracts date from YYYY-MM-DD format and returns a date object.
    """
    date_fragments = raw_date.split("-")
    return datetime.date(*[int(i) for i in date_fragments])
    