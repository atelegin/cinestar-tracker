import re
import logging
import os
import requests
import yaml
from functools import lru_cache
from typing import Optional

from src.state import load_state, save_state

logger = logging.getLogger(__name__)

# Markers to strip from title
STRIP_MARKERS = [
    r'\bOV\b', r'\bOmU\b', r'\bOmeU\b', r'\bOriginalfassung\b', r'\bOriginalversion\b',
    r'\b3D\b', r'\b2D\b', r'\bIMAX\b', r'\bDolby\b', r'\bAtmos\b'
]
STRIP_REGEX = re.compile('|'.join(STRIP_MARKERS), re.IGNORECASE)
GERMAN_HINT_REGEX = re.compile(
    r"[äöüß]|\b(der|die|das|und|oder|wenn|sie|ein|eine|im|am|vom|zum|zur|mit|ohne|für|ueber|über)\b",
    re.IGNORECASE
)
QUOTE_CHARS_REGEX = re.compile(r'["“”„«»]')
TITLE_SEPARATOR_REGEX = re.compile(r"\s[-–—]\s")

def normalize_title(title_raw: str) -> str:
    # 1. Strip markers
    cleaned = STRIP_REGEX.sub(' ', title_raw)
    # 1b. Remove decorative double quotes commonly used around EN title
    cleaned = QUOTE_CHARS_REGEX.sub('', cleaned)
    
    # 2. Clean empty brackets like () or [] caused by removal
    # Replaces ( ) with space, or () with empty
    cleaned = re.sub(r'\(\s*\)', ' ', cleaned)
    cleaned = re.sub(r'\[\s*\]', ' ', cleaned)
    
    # 3. Collapse whitespace and strip
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def build_search_variants(title_norm: str) -> list[str]:
    """
    Build fallback variants for TMDb search.
    Primary title is always first. For localized "DE - EN" / "EN - DE"
    patterns we also try the likely original-language half.
    """
    variants = []

    def add_variant(v: str):
        v = re.sub(r'\s+', ' ', v).strip()
        if v and v not in variants:
            variants.append(v)

    add_variant(title_norm)

    separator_match = TITLE_SEPARATOR_REGEX.search(title_norm)
    if separator_match:
        left, right = TITLE_SEPARATOR_REGEX.split(title_norm, maxsplit=1)
        left = left.strip()
        right = right.strip()
        left_looks_german = bool(GERMAN_HINT_REGEX.search(left))
        right_looks_german = bool(GERMAN_HINT_REGEX.search(right))

        if left and right:
            if left_looks_german and not right_looks_german:
                add_variant(right)
            elif right_looks_german and not left_looks_german:
                add_variant(left)
            else:
                add_variant(right)
                add_variant(left)

    return variants

@lru_cache(maxsize=1)
def load_overrides(path: str = "config/overrides.yaml") -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

def tmdb_search(title_norm: str, year: int = None, api_key: str = None) -> tuple[Optional[int], str]:
    if not api_key:
        return None, "no_api_key"

    url = "https://api.themoviedb.org/3/search/movie"

    # Strategy: First de-DE, then en-US
    languages = ["de-DE", "en-US"]
    THRESHOLD = 80 # High threshold as requested
    best_overall_score = -1
    # Cinema schedules are near-real-time, so without an explicit year we
    # bias toward recent releases instead of simply picking the most popular
    # match. Otherwise generic titles like "Michael" pick up the 1996 film
    # (TMDB id 2928) that has a huge vote_count.
    import datetime as _dt
    current_year = _dt.datetime.now().year

    def _cand_year(cand: dict) -> Optional[int]:
        rd = cand.get("release_date") or ""
        if len(rd) >= 4 and rd[:4].isdigit():
            return int(rd[:4])
        return None

    for query in build_search_variants(title_norm):
        candidates = []
        seen_ids = set()
        # Query both languages and merge: a recent local-language release
        # (e.g. an Indian "Michael" 2025) may only show up in en-US while
        # an older German/Austrian film dominates de-DE. Deduplicate by id.
        for lang in languages:
            params = {
                "api_key": api_key,
                "query": query,
                "language": lang
            }
            if year:
                params["year"] = year

            try:
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    for r in results:
                        rid = r.get("id")
                        if rid is None or rid in seen_ids:
                            continue
                        seen_ids.add(rid)
                        candidates.append(r)
            except Exception as e:
                logger.warning(f"TMDb search failed for {query} ({lang}): {e}")

        if not candidates:
            continue

        best_candidate = None
        best_score = -1
        query_lower = query.lower()

        for cand in candidates:
            score = 0
            cand_title = cand.get("title", "").lower()
            cand_orig = cand.get("original_title", "").lower()

            # Exact match
            if query_lower == cand_title or query_lower == cand_orig:
                score += 100
            # Substring
            elif query_lower in cand_title or query_lower in cand_orig:
                score += 30

            cand_year = _cand_year(cand)

            if year:
                # Explicit year comparison (strict; unchanged behavior).
                if cand_year is not None and cand_year == year:
                    score += 20
            else:
                # No input year: prefer recent releases, since the film is
                # actually playing in a multiplex right now. Older entries
                # (especially 30+ years) with the same exact title are almost
                # always wrong.
                if cand_year is not None:
                    age = current_year - cand_year
                    if age <= 3:
                        score += 25
                    elif age <= 10:
                        score += 0
                    elif age <= 30:
                        score -= 10
                    else:
                        score -= 20

            # Tie breaker: vote count kept as a *weak* signal only, so it
            # cannot overpower the recency bias above.
            score += min(cand.get("vote_count", 0) / 2000, 5)

            if score > best_score:
                best_score = score
                best_candidate = cand

        if best_score > best_overall_score:
            best_overall_score = best_score

        if best_candidate and best_score >= THRESHOLD:
            # Safety net: when we don't know the input year, refuse to return
            # a match that's more than ~15 years old. CineStar plays current
            # releases; a decade-old "Michael" (1996 or 2011) almost certainly
            # isn't the film actually on screen, and a missing Letterboxd
            # link is strictly better than one pointing at the wrong film.
            if not year:
                best_year = _cand_year(best_candidate)
                if best_year is not None and (current_year - best_year) > 15:
                    return None, f"best_too_old_{best_year}"
            if query == title_norm:
                return best_candidate["id"], "match"
            return best_candidate["id"], f"match_variant:{query}"

    if best_overall_score < 0:
        return None, "no_results"
    return None, f"low_score_{best_overall_score:.1f}"

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

@lru_cache(maxsize=256)
def _get_tmdb_details(tmdb_id: int, api_key: str = None) -> Optional[dict]:
    """Fetch /movie/{id} once and cache; helpers below read fields from it."""
    if not api_key:
        api_key = os.environ.get("TMDB_API_KEY")
    if not api_key or not tmdb_id:
        return None

    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {"api_key": api_key}

    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception as e:
        logger.warning(f"TMDb movie details failed for {tmdb_id}: {e}")
        return None


def get_tmdb_original_title(tmdb_id: int, api_key: str = None) -> Optional[str]:
    data = _get_tmdb_details(tmdb_id, api_key)
    if not data:
        return None
    original_title = data.get("original_title")
    return original_title.strip() if isinstance(original_title, str) and original_title.strip() else None


def get_tmdb_release_year(tmdb_id: int, api_key: str = None) -> Optional[int]:
    """Return the release year (int) for a TMDb movie id, or None."""
    data = _get_tmdb_details(tmdb_id, api_key)
    if not data:
        return None
    rd = data.get("release_date") or ""
    if len(rd) >= 4 and rd[:4].isdigit():
        return int(rd[:4])
    return None
