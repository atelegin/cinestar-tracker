"""Primary schedule source: CineStar's own JSON API.

kinoprogramm.com only lists the regular programme; previews, special
screenings and one-off OV/OmU shows (e.g. "Preview: You Can See Everything
(OmU)") exist only on cinestar.de. The site's frontend loads them from:

    GET https://www.cinestar.de/api/cinema/{cinema_id}/show/

which returns a list of shows (`_type` "movie" or "event"), each with
`showtimes[]` carrying a datetime ("2026-11-19 19:00 CET") and attribute
codes. Language codes seen in practice: OV, AUDIO_OV, OMU, AUDIO_OmU, SUBS,
LANG_EN/IT/FR; dubbed screenings carry only LANG_DE.
"""
import logging
import re
from datetime import datetime
from typing import Optional

import pytz
import requests

from src.parse_schedule import Session

logger = logging.getLogger(__name__)

BASE = "https://www.cinestar.de"
API_URL = BASE + "/api/cinema/{cinema_id}/show/"

OMU_CODES = {"OMU", "AUDIO_OmU", "SUBS"}
OV_CODES = {"OV", "AUDIO_OV"}

_PREFIX_RE = re.compile(r"^\s*(Preview|Vorpremiere|Sneak)\s*:\s*", re.I)
_LANG_PAREN_RE = re.compile(r"\(\s*(?:[a-zäöü]+\.?\s*)?(?:OmU|OmeU|OV)\s*\)", re.I)
_SERIES_SUFFIX_RE = re.compile(r"\s+-\s+Anime Nights \d{4}\s*$", re.I)


def version_label(attributes) -> str:
    codes = set(attributes or [])
    if codes & OMU_CODES:
        return "OmU"
    if codes & OV_CODES:
        return "OV"
    return "Deutsch"


def clean_title(title: str) -> str:
    t = _PREFIX_RE.sub("", title or "")
    t = _LANG_PAREN_RE.sub(" ", t)
    t = _SERIES_SUFFIX_RE.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_shows(shows: list, timezone_str: str = "Europe/Berlin") -> list[Session]:
    tz = pytz.timezone(timezone_str)

    # Previews are separate "event" entries but share the `movie` id with the
    # regular release; use the regular title so both group into one line.
    movie_titles = {
        s.get("movie"): s.get("title")
        for s in shows
        if s.get("_type") == "movie" and s.get("movie")
    }

    sessions = []
    for show in shows:
        kind = show.get("_type", "movie")
        title = movie_titles.get(show.get("movie")) or show.get("title") or "Unknown"
        title = clean_title(title)
        link = show.get("detailLink")
        film_url = f"{BASE}{link}" if link and link.startswith("/") else link

        for st in show.get("showtimes") or []:
            raw = (st.get("datetime") or "")[:16]
            try:
                dt = tz.localize(datetime.strptime(raw, "%Y-%m-%d %H:%M"))
            except ValueError:
                logger.warning(f"Bad showtime datetime: {st.get('datetime')!r}")
                continue
            s = Session(
                title_raw=title,
                dt_local=dt,
                film_url=film_url,
                tags_raw=version_label(st.get("attributes")),
            )
            s.kind = kind
            sessions.append(s)
    return sessions


def fetch_cinestar_sessions(
    cinema_id: int, timezone_str: str = "Europe/Berlin", timeout: int = 15
) -> Optional[list[Session]]:
    url = API_URL.format(cinema_id=cinema_id)
    try:
        logger.info(f"Fetching {url}")
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                         timeout=timeout)
        r.raise_for_status()
        shows = r.json()
        if not isinstance(shows, list):
            logger.error("CineStar API returned unexpected payload.")
            return None
    except (requests.RequestException, ValueError) as e:
        logger.error(f"CineStar API request failed: {e}")
        return None
    return parse_shows(shows, timezone_str)
