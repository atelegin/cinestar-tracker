import json
import os
import hashlib
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "state" / "state.json"

DEFAULT_STATE = {
    "last_sent_week_start": None,
    "last_hash": None,
    "sent_hashes_by_week": {},
    "tmdb_cache": {},
    "cinestar_cache": {}
}

MAX_SENT_HASH_HISTORY = 16


def load_state() -> dict:
    if not STATE_PATH.exists():
        return dict(DEFAULT_STATE)
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            logger.warning(f"State file at {STATE_PATH} is not a dict. Using default state.")
            return dict(DEFAULT_STATE)
        merged = dict(DEFAULT_STATE)
        merged.update(data)
        return merged
    except Exception as e:
        logger.warning(f"Failed to load state from {STATE_PATH}: {e}. Using default state.")
        return dict(DEFAULT_STATE)

def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(STATE_PATH.parent), encoding="utf-8") as f:
        f.write(payload)
        tmp = f.name
    os.replace(tmp, STATE_PATH)


def was_week_already_sent(state: dict, week_start_str: str, current_hash: str) -> bool:
    sent_hashes_by_week = state.get("sent_hashes_by_week")
    if isinstance(sent_hashes_by_week, dict) and week_start_str in sent_hashes_by_week:
        return sent_hashes_by_week.get(week_start_str) == current_hash

    if state.get("last_sent_week_start") != week_start_str:
        return False

    return state.get("last_hash") == current_hash


def record_sent_week(
    state: dict,
    week_start_str: str,
    current_hash: str,
    max_history: int = MAX_SENT_HASH_HISTORY,
) -> dict:
    state["last_sent_week_start"] = week_start_str
    state["last_hash"] = current_hash

    sent_hashes_by_week = state.get("sent_hashes_by_week")
    if not isinstance(sent_hashes_by_week, dict):
        sent_hashes_by_week = {}

    sent_hashes_by_week[week_start_str] = current_hash
    if len(sent_hashes_by_week) > max_history:
        oldest_weeks = sorted(sent_hashes_by_week.keys())[:-max_history]
        for old_week in oldest_weeks:
            sent_hashes_by_week.pop(old_week, None)

    state["sent_hashes_by_week"] = sent_hashes_by_week
    return state


def compute_content_hash(items: list[dict]) -> str:
    """
    Computes deterministic SHA256 hash of the content items.
    Items should be a list of dicts with: 
      title (normalized), session/sessions (obj(s) with dt_local), tmdb_id, cinestar_url
    """
    stable_list = []
    for item in items:
        sessions = item.get("sessions")
        if not sessions:
            sessions = [item['session']]

        dt_list = sorted(session.dt_local.isoformat() for session in sessions)
        
        stable_list.append({
            "title": item['title'],
            "dts": dt_list,
            "tmdb_id": item['tmdb_id'],
            "cinestar_url": item.get('cinestar_url') # Handles None gracefully
        })
        
    # Sort by title, then session list
    stable_list.sort(key=lambda x: (x['title'], tuple(x['dts'])))
    
    # Serialize with tight separators
    dump_str = json.dumps(stable_list, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    
    return hashlib.sha256(dump_str.encode('utf-8')).hexdigest()
