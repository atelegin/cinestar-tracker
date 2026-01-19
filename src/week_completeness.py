
from datetime import datetime, timedelta
from src.parse_schedule import Session

def is_week_complete(all_sessions: list[Session], week_start: datetime, week_end: datetime) -> bool:
    """
    Checks if the list of sessions covers the full week up to Wednesday.
    
    Args:
        all_sessions: List of ALL parsed sessions (not just OV).
        week_start: Thursday 00:00 (start of cinema week).
        week_end: Next Thursday 00:00 (exclusive end of cinema week).
        
    Returns:
        True if the maximum session date reaches at least the start of Wednesday 
        (week_end - 1 day). This implies the schedule horizon is far enough.
    """
    if not all_sessions:
        return False
        
    # We require data at least for Wednesday (the last day of the cinema week)
    # week_end is Thursday 00:00, so Wednesday 00:00 is week_end - 24h
    required_horizon = week_end - timedelta(days=1)
    
    max_dt = max(s.dt_local for s in all_sessions)
    
    # Ensure datetimes are comparable (timezone-aware)
    if required_horizon.tzinfo is None and max_dt.tzinfo is not None:
         # If week_end was naive, assume it's in the same timezone as max_dt (Berlin)
         required_horizon = required_horizon.replace(tzinfo=max_dt.tzinfo)
    elif required_horizon.tzinfo is not None and max_dt.tzinfo is None:
         # Should not happen based on parse_schedule, but for safety
         max_dt = max_dt.replace(tzinfo=required_horizon.tzinfo)

    return max_dt >= required_horizon
