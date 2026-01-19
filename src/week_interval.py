from datetime import datetime, timedelta, date

def compute_week_window(now: datetime) -> tuple[datetime, datetime]:
    """
    Returns (week_start, week_end) tuple.
    Rule:
    - If Mon-Wed (0-2): week_start is NEXT Thursday.
    - If Thu-Sun (3-6): week_start is CURRENT Thursday.
    
    Cinema week is Thu -> Next Wed.
    Window is [Thursday 00:00, Next Wednesday 23:59].
    """
    # weekday: Mon=0, ..., Thu=3, ..., Sun=6
    wd = now.weekday()
    today_date = now.date()
    
    if wd <= 2: # Mon, Tue, Wed
        # Days until next Thursday
        # Mon(0) -> +3 -> Thu(3)
        # Tue(1) -> +2 -> Thu(3)
        # Wed(2) -> +1 -> Thu(3)
        days_ahead = 3 - wd
        start_date = today_date + timedelta(days=days_ahead)
    else: # Thu, Fri, Sat, Sun
        # Days since last Thursday (or today)
        # Thu(3) -> -0
        # Fri(4) -> -1
        # Sun(6) -> -3
        days_back = wd - 3
        start_date = today_date - timedelta(days=days_back)
        
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
