
import pytest
from datetime import datetime, timedelta
import pytz
from src.parse_schedule import Session
from src.week_completeness import is_week_complete

def test_week_incomplete_empty():
    tz = pytz.timezone("Europe/Berlin")
    week_start = tz.localize(datetime(2026, 1, 15)) # Thu
    week_end = tz.localize(datetime(2026, 1, 22))   # Thu
    
    assert is_week_complete([], week_start, week_end) is False

def test_week_incomplete_short_horizon():
    tz = pytz.timezone("Europe/Berlin")
    week_start = tz.localize(datetime(2026, 1, 15)) # Thu
    week_end = tz.localize(datetime(2026, 1, 22))   # Thu
    
    # Max session on Sunday 18th
    sessions = [
        Session("Movie 1", week_start, "url", "tag"),
        Session("Movie 2", week_start + timedelta(days=3), "url", "tag") # Sunday
    ]
    
    assert is_week_complete(sessions, week_start, week_end) is False

def test_week_complete_exact_horizon():
    tz = pytz.timezone("Europe/Berlin")
    week_start = tz.localize(datetime(2026, 1, 15)) # Thu
    week_end = tz.localize(datetime(2026, 1, 22))   # Thu
    
    # Max session on Wednesday 21st 00:00 (start of day)
    # This meets the condition >= week_end - 1 day
    wed_start = week_end - timedelta(days=1)
    
    sessions = [
        Session("Movie 1", week_start, "url", "tag"),
        Session("Movie 2", wed_start, "url", "tag") 
    ]
    
    assert is_week_complete(sessions, week_start, week_end) is True

def test_week_complete_far_horizon():
    tz = pytz.timezone("Europe/Berlin")
    week_start = tz.localize(datetime(2026, 1, 15)) # Thu
    week_end = tz.localize(datetime(2026, 1, 22))   # Thu
    
    # Max session on Wednesday 21st 23:00
    wed_late = week_end - timedelta(hours=1)
    
    sessions = [
        Session("Movie 1", week_start, "url", "tag"),
        Session("Movie 2", wed_late, "url", "tag") 
    ]
    
    assert is_week_complete(sessions, week_start, week_end) is True
