from datetime import datetime
from typing import Optional


def format_date_ru(dt: datetime) -> str:
    """
    Format: 'Пн 19.01 14:30' (без запятой, компактнее)
    """
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    day_str = days[dt.weekday()]
    return f"{day_str} {dt.strftime('%d.%m %H:%M')}"


def format_message(
    week_start: datetime,
    week_end: datetime,
    items: list[dict],
) -> str:
    """
    items: list of dicts {
        'title': str (clean),
        'session': Session obj,
        'tmdb_id': int|None,
        'cinestar_url': str|None   # может быть и fallback на kinoprogramm
    }
    """
    start_str = week_start.strftime("%d.%m")
    end_str = week_end.strftime("%d.%m")

    # Заголовок короче и чище
    lines = [f"🎬 CineStar Konstanz — OV ({start_str}–{end_str})"]

    if not items:
        lines.append("На этой неделе OV-сеансов не найдено.")
        return "\n".join(lines)

    for item in items:
        title = item["title"]
        s = item["session"]
        link_url = item.get("cinestar_url")  # preferred CineStar, иначе fallback
        tmdb_id = item.get("tmdb_id")

        date_ru = format_date_ru(s.dt_local)

        links = []
        if link_url:
            links.append(f"[🎟 Билеты]({link_url})")
        if tmdb_id:
            links.append(f"[🎞 LB](https://letterboxd.com/tmdb/{tmdb_id}/)")

        if links:
            lines.append(f"• {title} — {date_ru} — " + " · ".join(links))
        else:
            lines.append(f"• {title} — {date_ru}")

    return "\n".join(lines)
