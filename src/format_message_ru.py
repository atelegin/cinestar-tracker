from datetime import datetime
from html import escape

DAY_NAMES_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

def format_date_ru(dt: datetime) -> str:
    return f"{DAY_NAMES_RU[dt.weekday()]} {dt.strftime('%d.%m %H:%M')}"

def format_day_ru(dt: datetime) -> str:
    return DAY_NAMES_RU[dt.weekday()]

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
    grouped_sessions = []
    current_dt = ordered_sessions[0].dt_local
    current_date = current_dt.date()
    current_times = []

    for session in ordered_sessions:
        dt = session.dt_local
        session_date = dt.date()
        if current_date != session_date:
            grouped_sessions.append(f"{format_day_ru(current_dt)} {', '.join(current_times)}")
            current_date = session_date
            current_dt = dt
            current_times = []
        current_times.append(dt.strftime("%H:%M"))

    if current_times:
        grouped_sessions.append(f"{format_day_ru(current_dt)} {', '.join(current_times)}")

    return "; ".join(grouped_sessions)

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
        title_html = title
        if tmdb_id:
            title_html = f'<a href="https://letterboxd.com/tmdb/{tmdb_id}/">{title}</a>'

        links = []
        if ticket_url:
            links.append(f'<a href="{escape(ticket_url)}">⭐ Билеты</a>')

        # одна строка, очень компактно
        tail = f" — {' · '.join(links)}" if links else ""
        lines.append(f"• {title_html} — {dt}{tail}")

    return "\n".join(lines)
