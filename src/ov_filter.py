from .parse_schedule import Session

def filter_ov_sessions(sessions: list[Session], markers: list[str]) -> list[Session]:
    filtered = []
    markers_lower = [m.lower() for m in markers]
    
    for s in sessions:
        # Check title and tags (tags currently = title_raw)
        # Search anywhere in the string
        text_to_search = (s.title + " " + (s.tags or "")).lower()
        
        is_ov = any(m in text_to_search for m in markers_lower)
        
        if is_ov:
            filtered.append(s)
            
    return filtered
