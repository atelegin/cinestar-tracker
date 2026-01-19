from datetime import datetime
from typing import Optional

def format_date_ru(dt: datetime) -> str:
    """
    Format: 'Пн 19.01, 14:30'
    """
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    day_str = days[dt.weekday()]
    return f"{day_str} {dt.strftime('%d.%m, %H:%M')}"

def format_message(
    week_start: datetime, 
    week_end: datetime, 
    items: list[dict]
) -> str:
    """
    items: list of dicts {
        'title': str (clean),
        'session': Session obj, 
        'tmdb_id': int|None,
        'cinestar_url': str|None
    }
    """
    start_str = week_start.strftime("%d.%m")
    end_str = week_end.strftime("%d.%m")
    
    lines = [f"🎬 CineStar Konstanz — OV (кинонеделя {start_str}–{end_str})"]
    lines.append("Источник: [kinoprogramm.com](https://www.kinoprogramm.com/kino/konstanz-universitaetsstadt/cinestar-konstanz-60996)\n")
    
    if not items:
        lines.append("На этой неделе OV-сеансов не найдено.")
        return "\n".join(lines)

    for item in items:
        title = item['title']
        s = item['session']
        cinestar_url = item['cinestar_url']
        tmdb_id = item['tmdb_id']
        
        # Line 1: • Title (Year) — Day DD.MM, HH:MM
        # We don't have year easily in session title, but user requested clean title.
        date_ru = format_date_ru(s.dt_local)
        
        # Link to session on film page if we have a URL, or just title
        # "• <Title> (OV) — <Date>"
        # Add (OV) marker if not present? Or just keep it assuming context is OV.
        # User asked: "• <Название> (OV) — <День_недели_RU> DD.MM, HH:MM"
        
        lines.append(f"• {title} (OV) — {date_ru}")
        
        # Line 2 links
        links = []
        if cinestar_url and 'cinestar.de' in cinestar_url:
            links.append(f"[CineStar]({cinestar_url})")
        elif cinestar_url:
             links.append(f"[Kinoprogramm]({cinestar_url})") # Fallback link source
             
        if tmdb_id:
            links.append(f"[Letterboxd](https://letterboxd.com/tmdb/{tmdb_id}/)")
            
        if links:
            lines.append("  " + " | ".join(links))
            
    return "\n".join(lines)
