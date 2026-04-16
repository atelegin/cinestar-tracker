from typing import Optional
import re
import datetime
import requests
import logging
import unicodedata

logger = logging.getLogger(__name__)
TITLE_SEPARATOR_REGEX = re.compile(r"\s[-–—]\s")
# "<b>Produktionsjahr</b><span>2011</span>" on CineStar film pages.
PRODUKTIONSJAHR_REGEX = re.compile(
    r"Produktionsjahr\s*</b>\s*<span[^>]*>\s*(\d{4})\s*</span>",
    re.IGNORECASE,
)
# How old a CineStar film page may be (vs. current year) when we have no
# TMDb year to compare against. CineStar leaves old film detail pages live
# forever, so without this guard a zombie page like /film/michael (2011)
# would be accepted just because its slug collides with a new release.
MAX_PAGE_AGE_NO_EXPECTED_YEAR = 4

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

def slugify_cinestar_loose(title: str) -> str:
    """
    Fallback slugifier for CineStar pages that drop umlauts instead of using ae/oe/ue.
    """
    t = unicodedata.normalize("NFKD", title.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.replace('ß', 'ss')
    t = re.sub(r'[^a-z0-9]+', '-', t)
    t = re.sub(r'-+', '-', t).strip('-')
    return t

def build_cinestar_slug_candidates(title_norm: str, original_title: Optional[str] = None) -> list[str]:
    title_candidates = []
    slug_candidates = []

    def add_title_candidate(candidate_title: str) -> None:
        candidate_title = candidate_title.strip()
        if candidate_title and candidate_title not in title_candidates:
            title_candidates.append(candidate_title)

    def add_slug_candidate(slug: str) -> None:
        if slug and slug not in slug_candidates:
            slug_candidates.append(slug)

    add_title_candidate(title_norm)

    if TITLE_SEPARATOR_REGEX.search(title_norm):
        left, right = TITLE_SEPARATOR_REGEX.split(title_norm, maxsplit=1)
        add_title_candidate(left)
        add_title_candidate(right)

    if original_title and original_title.strip():
        add_title_candidate(f"{title_norm} - {original_title.strip()}")
        add_title_candidate(original_title)

    for candidate_title in title_candidates:
        add_slug_candidate(slugify_cinestar(candidate_title))
        add_slug_candidate(slugify_cinestar_loose(candidate_title))

    return slug_candidates

def _parse_produktionsjahr(html: str) -> Optional[int]:
    """Extract CineStar's 'Produktionsjahr' (production year) from film page HTML."""
    m = PRODUKTIONSJAHR_REGEX.search(html)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _year_confirms_page(
    page_year: Optional[int], expected_year: Optional[int]
) -> bool:
    """Decide whether a CineStar film page matches the movie we meant."""
    if expected_year is not None:
        # We know the TMDb year: require the page's Produktionsjahr to match.
        # CineStar sometimes lists a different Produktionsjahr than TMDb
        # (co-productions, festival vs. release year), so allow ±1.
        if page_year is None:
            # Page has no Produktionsjahr — can't confirm. Reject to stay safe;
            # the kinoprogramm fallback is always correct.
            return False
        return abs(page_year - expected_year) <= 1

    # No expected year: accept only if the page looks recent enough not to be
    # a zombie detail page for an unrelated older film with the same slug.
    if page_year is None:
        return True
    current_year = datetime.datetime.now().year
    return (current_year - page_year) <= MAX_PAGE_AGE_NO_EXPECTED_YEAR


def resolve_cinestar_url(
    title_norm: str,
    kinoprogramm_film_url: Optional[str],
    original_title: Optional[str] = None,
    expected_year: Optional[int] = None,
) -> Optional[str]:
    """
    Resolve a CineStar Konstanz film URL by slug-guessing from the title.

    A plain `HEAD 200` check is not enough: CineStar keeps old film detail
    pages online indefinitely, so a slug like `/film/michael` can collide
    with a decade-old page for an unrelated film. To avoid that, we GET the
    page and compare its 'Produktionsjahr' to `expected_year` (typically the
    TMDb release year). If it doesn't line up, we reject the candidate and
    fall back to the kinoprogramm URL which is always correct.

    Example of a correct resolution:
      https://www.cinestar.de/kino-konstanz/film/avatar-fire-and-ash
    Example of a zombie collision we now reject:
      /film/michael → a 2011 Austrian film, not the 2025 release playing now.
    """

    # Base URL for CineStar Konstanz
    base_url = "https://www.cinestar.de/kino-konstanz/film"

    candidates = build_cinestar_slug_candidates(title_norm, original_title)

    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    for cand in candidates:
        url = f"{base_url}/{cand}"
        try:
            resp = requests.get(url, headers=headers, timeout=3, allow_redirects=True)
            if resp.status_code != 200:
                continue
            page_year = _parse_produktionsjahr(resp.text)
            if _year_confirms_page(page_year, expected_year):
                return url
            logger.info(
                "Rejecting CineStar URL %s: page_year=%s, expected_year=%s",
                url, page_year, expected_year,
            )
        except Exception:
            pass  # Ignore connection errors

    # Fallback
    return kinoprogramm_film_url
