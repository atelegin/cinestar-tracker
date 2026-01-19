from datetime import datetime, timedelta, date

def compute_week_window(now: datetime) -> tuple[datetime, datetime]:
    """
    Returns (week_start, week_end) tuple for the CURRENT cinema week.
    Cinema week is Thu -> Next Wed.
    
    Logic: Always find the most recent Thursday (or today if today is Thursday).
    Window is [Thursday 00:00, Next Wednesday 23:59].
    """
    # weekday: Mon=0, ..., Thu=3, ..., Sun=6
    wd = now.weekday()
    today_date = now.date()
    
    # Calculate days since the last Thursday
    # Thu(3) -> 0
    # Fri(4) -> 1
    # ...
    # Wed(2) -> 6
    # Math: (wd - 3) % 7
    days_since_thu = (wd - 3) % 7
    
    start_date = today_date - timedelta(days=days_since_thu)
        
    start_dt = datetime.combine(start_date, datetime.min.time())
    # End is +6 days (Wed) at 23:59
    end_dt = datetime.combine(start_date + timedelta(days=6), datetime.max.time())
    
    return start_dt, end_dt

def filter_by_week(sessions: list, week_start: datetime, week_end: datetime) -> list:
    """
    Filters sessions that fall within [week_start, week_end] inclusive.
    Assumes session.dt_local is timezone-aware and comparable if week_start is too.
    However, compute_week_window returns native datetimes. 
    We should normalize.
    """
    filtered = []
    # Make naive for comparison or localize window?
    # Session dt is timezone aware (Europe/Berlin).
    # Let's make window timezone aware if possible, or strip tz from session.
    # Given we work in specific timezone, simpler to strip TZ from session for comparison 
    # OR assume input is correct.
    
    # Ideally, week_start/end should be localized to the same timezone as sessions.
    # But for MVP, simple comparison:
    
    for s in sessions:
        # s.dt_local is aware.
        # week_start is naive (from compute_week_window).
        # Localize week_start/end to session's tokenizer or naive-ify session
        
        s_dt = s.dt_local.replace(tzinfo=None) # naive in local time
        if week_start <= s_dt <= week_end:
            filtered.append(s)
            
    return filtered
