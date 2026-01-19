from datetime import datetime
from html import escape

def format_date_ru(dt: datetime) -> str:
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    return f"{days[dt.weekday()]} {dt.strftime('%d.%m %H:%M')}"

def _week_range_compact(week_start: datetime, week_end: datetime) -> str:
    # week_end ожидается как конец окна (следующий четверг), показываем до среды:
    end = week_end.replace(hour=0, minute=0, second=0, microsecond=0)
    end_minus_1 = end.fromtimestamp(end.timestamp() - 24*3600)
    if week_start.month == end_minus_1.month:
        return f"{week_start.day}–{end_minus_1.strftime('%d.%m')}"
    return f"{week_start.strftime('%d.%m')}–{end_minus_1.strftime('%d.%m')}"

def format_message(week_start: datetime, week_end: datetime, items: list[dict]) -> str:
    header = f"🎬 CineStar Konstanz — OV ({_week_range_compact(week_start, week_end)})"
    lines = [header, ""]

    if not items:
        lines.append("OV-сеансов не найдено.")
        return "\n".join(lines)

    for item in items:
        title = escape(item["title"])
        s = item["session"]
        dt = format_date_ru(s.dt_local)

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
