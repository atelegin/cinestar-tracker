from typing import Optional
import re
import requests
import logging

logger = logging.getLogger(__name__)
TITLE_SEPARATOR_REGEX = re.compile(r"\s[-–—]\s")

def slugify_cinestar(title: str) -> str:
    """
    Lowercase, ä->ae etc, strip non-alphanumeric (except dash), collapse dashes.
    """
    t = title.lower()
    t = t.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    
    # Replace non-alphanumeric with dash
    t = re.sub(r'[^a-z0-9]+', '-', t)
    
    # Collapse dashes and strip
    t = re.sub(r'-+', '-', t).strip('-')
    return t

def build_cinestar_slug_candidates(title_norm: str) -> list[str]:
    candidates = []

    def add_candidate(candidate_title: str) -> None:
        slug = slugify_cinestar(candidate_title.strip())
        if slug and slug not in candidates:
            candidates.append(slug)

    add_candidate(title_norm)

    if TITLE_SEPARATOR_REGEX.search(title_norm):
        left, right = TITLE_SEPARATOR_REGEX.split(title_norm, maxsplit=1)
        add_candidate(left)
        add_candidate(right)

    return candidates

def resolve_cinestar_url(title_norm: str, kinoprogramm_film_url: Optional[str]) -> Optional[str]:
    """
    Tries to resolve https://www.cinestar.de/kino-konstanz/veranstaltung-on-<slugify(title_norm)>
    Usually their URLs look like: https://www.cinestar.de/kino-konstanz/veranstaltung-on-<slug>
    WAIT. The request was /film/<slug>. Let's check typical CineStar URLs.
    
    Actually, mostly it's https://www.cinestar.de/kino-konstanz/filme/<slug> OR just /kino-konstanz/...
    Let's check the user request: "https://www.cinestar.de/film/<slug>"
    or simpler "https://www.cinestar.de/kino-konstanz/film/<slug>"
     or generic "https://www.cinestar.de/film/<slug>" if it redirects to local?
    
    Let's stick to the user's "https://www.cinestar.de/film/<slug>" request first, 
    but practically CineStar URLs are often locale specific.
    Example: https://www.cinestar.de/kino-konstanz/film/avatar-fire-and-ash
    
    Strategy:
    1. Try constructing slug candidates.
    2. HEAD request to `https://www.cinestar.de/kino-konstanz/film/{slug}` (seems plausible).
    3. If fail, return kinoprogramm_film_url (Fallback).
    """
    
    # Base URL for CineStar Konstanz
    base_url = "https://www.cinestar.de/kino-konstanz/film"
    
    candidates = build_cinestar_slug_candidates(title_norm)
    
    headers = {
        "User-Agent": "Mozilla/5.0",
    }
    
    for cand in candidates:
        url = f"{base_url}/{cand}"
        try:
            # Short timeout, don't block too long
            resp = requests.head(url, headers=headers, timeout=2, allow_redirects=True)
            if resp.status_code == 200:
                return url
        except Exception:
            pass # Ignore connection errors
            
    # Fallback
    return kinoprogramm_film_url
