from datetime import datetime
from html import escape

def format_date_ru(dt: datetime) -> str:
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    return f"{days[dt.weekday()]} {dt.strftime('%d.%m %H:%M')}"

def _week_range_compact(week_start: datetime, week_end: datetime) -> str:
    # week_end is actually next Thursday (start + 7 days) in kinoprogramm logic
    # We want to display Thu -> Wed (which is start + 6 days)
    from datetime import timedelta
    display_end = week_start + timedelta(days=6)
    
    if week_start.month == display_end.month:
        return f"{week_start.day}–{display_end.strftime('%d.%m')}"
    return f"{week_start.strftime('%d.%m')}–{display_end.strftime('%d.%m')}"

def _format_sessions_ru(item: dict) -> str:
    sessions = item.get("sessions")
    if not sessions:
        sessions = [item["session"]]

    ordered_sessions = sorted(sessions, key=lambda session: session.dt_local)
    return ", ".join(format_date_ru(session.dt_local) for session in ordered_sessions)

def format_message(week_start: datetime, week_end: datetime, items: list[dict]) -> str:
    header = f"🎬 CineStar Konstanz — OV ({_week_range_compact(week_start, week_end)})"
    lines = [header, ""]

    if not items:
        lines.append("OV-сеансов не найдено.")
        return "\n".join(lines)

    for item in items:
        title = escape(item["title"])
        dt = _format_sessions_ru(item)

        ticket_url = item.get("cinestar_url")  # CineStar preferred, иначе fallback (kinoprogramm)
        tmdb_id = item.get("tmdb_id")

        links = []
        if ticket_url:
            links.append(f'<a href="{escape(ticket_url)}">🎟 Билеты</a>')
        if tmdb_id:
            links.append(f'<a href="https://letterboxd.com/tmdb/{tmdb_id}/">🎞 LB</a>')

        # одна строка, очень компактно
        tail = f" — {' · '.join(links)}" if links else ""
        lines.append(f"• {title} — {dt}{tail}")

    return "\n".join(lines)
