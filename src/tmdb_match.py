import re
import logging
import os
import requests
import yaml
import json
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Markers to strip from title
STRIP_MARKERS = [
    r'\bOV\b', r'\bOmU\b', r'\bOmeU\b', r'\bOriginalfassung\b', r'\bOriginalversion\b',
    r'\b3D\b', r'\b2D\b', r'\bIMAX\b', r'\bDolby\b', r'\bAtmos\b'
]
STRIP_REGEX = re.compile('|'.join(STRIP_MARKERS), re.IGNORECASE)

def normalize_title(title_raw: str) -> str:
    # 1. Strip markers
    cleaned = STRIP_REGEX.sub(' ', title_raw)
    
    # 2. Clean empty brackets like () or [] caused by removal
    # Replaces ( ) with space, or () with empty
    cleaned = re.sub(r'\(\s*\)', ' ', cleaned)
    cleaned = re.sub(r'\[\s*\]', ' ', cleaned)
    
    # 3. Collapse whitespace and strip
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

@lru_cache(maxsize=1)
def load_overrides(path: str = "config/overrides.yaml") -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

def load_state(path: str = "state/state.json") -> dict:
    if not os.path.exists(path):
        return {"tmdb_cache": {}}
    with open(path, "r") as f:
        return json.load(f)

def save_state(state: dict, path: str = "state/state.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)

def tmdb_search(title_norm: str, year: int = None, api_key: str = None) -> tuple[Optional[int], str]:
    if not api_key:
        return None, "no_api_key"

    url = "https://api.themoviedb.org/3/search/movie"
    
    # Strategy: First de-DE, then en-US
    languages = ["de-DE", "en-US"]
    candidates = []

    for lang in languages:
        params = {
            "api_key": api_key,
            "query": title_norm,
            "language": lang
        }
        if year:
            params["year"] = year
            
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    candidates.extend(results)
                    # If we found something in DE, maybe that's enough? 
                    # But verifying against EN might be good for better scoring if DE title is weird.
                    # For MVP, if we have results in DE, let's process them.
                    break 
        except Exception as e:
            logger.warning(f"TMDb search failed for {title_norm} ({lang}): {e}")
            
    if not candidates:
        return None, "no_results"

    # Scoring
    best_candidate = None
    best_score = -1
    
    norm_lower = title_norm.lower()

    for cand in candidates:
        score = 0
        cand_title = cand.get("title", "").lower()
        cand_orig = cand.get("original_title", "").lower()
        cand_id = cand.get("id")
        
        # Exact match
        if norm_lower == cand_title or norm_lower == cand_orig:
            score += 100
        # Substring
        elif norm_lower in cand_title or norm_lower in cand_orig:
            score += 30
            
        # Year match (+- 1 year tolerance could be added, but stricter for now)
        if year and cand.get("release_date"):
            cand_year = cand["release_date"][:4]
            if str(year) == cand_year:
                score += 20
        
        # Tie breaker: vote count (normalized slightly to not dominate)
        # We just add a fraction of it or use it as standard tie breaker
        # Simple policy: score + (vote_count / 10000) max 10 points
        score += min(cand.get("vote_count", 0) / 1000, 10)

        if score > best_score:
            best_score = score
            best_candidate = cand

    THRESHOLD = 80 # High threshold as requested
    if best_score >= THRESHOLD:
        return best_candidate["id"], "match"
    
    return None, f"low_score_{best_score:.1f}"

def resolve_tmdb_id(title_norm: str, year: int = None) -> tuple[Optional[int], str]:
    # 1. Overrides
    overrides = load_overrides()
    if title_norm in overrides:
        return overrides[title_norm], "override"

    # 2. Cache
    state = load_state()
    cache = state.get("tmdb_cache", {})
    if title_norm in cache:
        return cache[title_norm], "cache"

    # 3. Search
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        return None, "no_api_key_env"

    tmdb_id, reason = tmdb_search(title_norm, year, api_key)
    
    if tmdb_id:
        # Update Cache
        cache[title_norm] = tmdb_id
        state["tmdb_cache"] = cache # ensure key exists
        save_state(state)
        return tmdb_id, reason # 'match'

    return None, reason
