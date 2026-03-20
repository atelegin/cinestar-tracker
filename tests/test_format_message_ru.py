from datetime import datetime

import pytz

from src.format_message_ru import format_message
from src.parse_schedule import Session


def test_format_message_lists_all_sessions_for_one_title():
    tz = pytz.timezone("Europe/Berlin")
    week_start = datetime(2026, 3, 19)
    week_end = datetime(2026, 3, 26)

    first = Session(
        "Der Astronaut - Project Hail Mary [Originalfassung]",
        tz.localize(datetime(2026, 3, 21, 22, 45)),
        "https://example.com/project-hail-mary",
        "Originalfassung",
    )
    second = Session(
        "Der Astronaut - Project Hail Mary [Originalfassung]",
        tz.localize(datetime(2026, 3, 22, 19, 45)),
        "https://example.com/project-hail-mary",
        "Originalfassung",
    )

    message = format_message(
        week_start,
        week_end,
        [
            {
                "title": "Der Astronaut - Project Hail Mary",
                "session": first,
                "sessions": [first, second],
                "tmdb_id": 687163,
                "cinestar_url": "https://example.com/project-hail-mary",
            }
        ],
    )

    assert "Сб 21.03 22:45, Вс 22.03 19:45" in message
    assert '<a href="https://letterboxd.com/tmdb/687163/">Der Astronaut - Project Hail Mary</a>' in message
    assert "🎞 LB" not in message
