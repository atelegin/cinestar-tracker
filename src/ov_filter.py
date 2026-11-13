from .parse_schedule import Session

def filter_ov_sessions(sessions: list[Session], markers: list[str]) -> list[Session]:
    filtered = []
    markers_lower = [m.lower() for m in markers]
    
    for s in sessions:
        # Version label from kinoprogramm.com ("Originalfassung", "Original mit
        # Untertiteln", "Deutsch"). Title is not searched: short markers like
        # "ov" would match inside words ("Love", "November").
        text_to_search = (s.tags or "").lower()
        
        is_ov = any(m in text_to_search for m in markers_lower)
        
        if is_ov:
            filtered.append(s)
            
    return filtered
