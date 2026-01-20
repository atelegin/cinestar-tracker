import json
import os
import hashlib
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "state" / "state.json"

DEFAULT_STATE = {
    "last_sent_week_start": None,
    "last_hash": None,
    "tmdb_cache": {},
    "cinestar_cache": {}
}

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

def compute_content_hash(items: list[dict]) -> str:
    """
    Computes deterministic SHA256 hash of the content items.
    Items should be a list of dicts with: 
      title (normalized), session (obj with dt_local), tmdb_id, cinestar_url
    """
    stable_list = []
    for item in items:
        s = item['session']
        # Convert dt to isoformat string
        dt_str = s.dt_local.isoformat()
        
        stable_list.append({
            "title": item['title'],
            "dt": dt_str,
            "tmdb_id": item['tmdb_id'],
            "cinestar_url": item.get('cinestar_url') # Handles None gracefully
        })
        
    # Sort by title, then dt
    stable_list.sort(key=lambda x: (x['title'], x['dt']))
    
    # Serialize with tight separators
    dump_str = json.dumps(stable_list, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    
    return hashlib.sha256(dump_str.encode('utf-8')).hexdigest()
