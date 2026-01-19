import json
import os
import hashlib
from typing import Optional, Dict

STATE_PATH = "state/state.json"

def load_state(path: str = STATE_PATH) -> dict:
    if not os.path.exists(path):
        return {
            "last_sent_week_start": None,
            "last_hash": None,
            "tmdb_cache": {},
            "cinestar_cache": {}
        }
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state: dict, path: str = STATE_PATH):
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)

def compute_content_hash(items: list[dict]) -> str:
    """
    Computes deterministic SHA256 hash of the content items.
    Items should be a list of dicts with: 
      title (normalized), session (obj with dt_local), tmdb_id, cinestar_url
    """
    # Extract stable representation
    stable_list = []
    for item in items:
        s = item['session']
        # Convert dt to isoformat string, assuming it has tzinfo or is normalized
        dt_str = s.dt_local.isoformat()
        
        stable_item = {
            "title": item['title'],
            "dt": dt_str,
            "tmdb_id": item['tmdb_id'],
            "cinestar_url": item.get('cinestar_url')
        }
        stable_list.append(stable_item)
        
    # Sort by title, then dt
    stable_list.sort(key=lambda x: (x['title'], x['dt']))
    
    # Serialize
    dump_str = json.dumps(stable_list, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    
    return hashlib.sha256(dump_str.encode('utf-8')).hexdigest()
