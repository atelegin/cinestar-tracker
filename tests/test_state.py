from datetime import datetime
from types import SimpleNamespace

import pytz

from src.state import (
    MAX_SENT_HASH_HISTORY,
    compute_content_hash,
    record_sent_week,
    was_week_already_sent,
)


def _item(title: str, year: int, month: int, day: int, hour: int, tmdb_id: int, url: str) -> dict:
    tz = pytz.timezone("Europe/Berlin")
    session = SimpleNamespace(dt_local=tz.localize(datetime(year, month, day, hour, 0)))
    return {
        "title": title,
        "session": session,
        "tmdb_id": tmdb_id,
        "cinestar_url": url,
    }


def test_compute_content_hash_is_order_independent():
    item_a = _item("Movie A", 2026, 3, 12, 14, 101, "https://example.com/a")
    item_b = _item("Movie B", 2026, 3, 14, 22, 202, "https://example.com/b")

    assert compute_content_hash([item_a, item_b]) == compute_content_hash([item_b, item_a])


def test_was_week_already_sent_checks_week_hash_history():
    state = {
        "last_sent_week_start": "2026-03-19",
        "last_hash": "hash-2",
        "sent_hashes_by_week": {
            "2026-03-12": "hash-1",
            "2026-03-19": "hash-2",
        },
    }

    assert was_week_already_sent(state, "2026-03-12", "hash-1") is True
    assert was_week_already_sent(state, "2026-03-12", "hash-x") is True


def test_was_week_already_sent_blocks_any_repeat_for_same_week():
    state = {
        "last_sent_week_start": "2026-03-19",
        "last_hash": "hash-2",
        "sent_hashes_by_week": {
            "2026-03-19": "hash-2",
        },
    }

    assert was_week_already_sent(state, "2026-03-19", "hash-2") is True
    assert was_week_already_sent(state, "2026-03-19", "hash-3") is True


def test_record_sent_week_updates_and_prunes_history():
    state = {
        "sent_hashes_by_week": {
            f"2026-01-{day:02d}": f"hash-{day}"
            for day in range(1, MAX_SENT_HASH_HISTORY + 2)
        }
    }

    updated = record_sent_week(state, "2026-03-12", "current-hash", max_history=MAX_SENT_HASH_HISTORY)

    assert updated["last_sent_week_start"] == "2026-03-12"
    assert updated["last_hash"] == "current-hash"
    assert updated["sent_hashes_by_week"]["2026-03-12"] == "current-hash"
    assert len(updated["sent_hashes_by_week"]) == MAX_SENT_HASH_HISTORY
    assert "2026-01-01" not in updated["sent_hashes_by_week"]


def test_compute_content_hash_changes_when_session_list_changes():
    first = _item("Movie A", 2026, 3, 21, 22, 101, "https://example.com/a")
    second_session = SimpleNamespace(
        dt_local=pytz.timezone("Europe/Berlin").localize(datetime(2026, 3, 22, 19, 0))
    )
    expanded = {
        **first,
        "sessions": [first["session"], second_session],
    }

    assert compute_content_hash([first]) != compute_content_hash([expanded])
