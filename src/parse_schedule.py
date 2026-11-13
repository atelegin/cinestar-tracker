import logging
import re
from datetime import datetime

import pytz
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.kinoprogramm.com"
TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


class Session:
    def __init__(self, title_raw, dt_local, film_url, tags_raw):
        self.title = title_raw
        self.dt_local = dt_local
        self.film_url = film_url
        self.tags = tags_raw

    def __repr__(self):
        return f"<Session {self.title} @ {self.dt_local} [{self.tags}]>"


def _abs_url(href):
    if not href:
        return None
    return f"{BASE_URL}{href}" if href.startswith("/") else href


def parse_schedule(html_content: str, timezone_str: str = "Europe/Berlin") -> list[Session]:
    """Parse kinoprogramm.com cinema page (layout since autumn 2026).

    Structure:
      <article data-kino-week-film id="film-...">
        <a class="text-lg ..." href="/kino/.../film-slug">Title</a>
        <section class="kino-week-day" data-kino-week-day="YYYY-MM-DD">
          <div data-kino-week-version="originalfassung">
            <p>Originalfassung</p>
            <span class="kino-week-time">19:30</span>
          </div>
        </section>
      </article>

    `tags` carries the version label (e.g. "Deutsch", "Originalfassung",
    "Original mit Untertiteln"), which the OV filter checks.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    tz = pytz.timezone(timezone_str)
    sessions = []

    films = soup.find_all("article", attrs={"data-kino-week-film": True})
    if not films:
        logger.warning("No film blocks found — kinoprogramm.com layout may have changed.")

    for film in films:
        title_raw = "Unknown"
        film_url = None
        title_link = None
        for a in film.find_all("a", href=True):
            if "kino-week-poster" in (a.get("class") or []):
                continue
            if a.get_text(strip=True):
                title_link = a
                break
        if title_link:
            title_raw = title_link.get_text(strip=True)
            film_url = _abs_url(title_link["href"])

        for day in film.find_all("section", attrs={"data-kino-week-day": True}):
            day_str = day["data-kino-week-day"]
            try:
                day_date = datetime.strptime(day_str, "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Bad day attribute: {day_str}")
                continue

            for version in day.find_all(attrs={"data-kino-week-version": True}):
                label_p = version.find("p")
                label = label_p.get_text(strip=True) if label_p else version["data-kino-week-version"]

                for t in version.find_all("span", class_="kino-week-time"):
                    m = TIME_RE.match(t.get_text(strip=True))
                    if not m:
                        continue
                    dt_naive = datetime(day_date.year, day_date.month, day_date.day,
                                        int(m.group(1)), int(m.group(2)))
                    sessions.append(Session(
                        title_raw=title_raw,
                        dt_local=tz.localize(dt_naive),
                        film_url=film_url,
                        tags_raw=label,
                    ))

    return sessions
