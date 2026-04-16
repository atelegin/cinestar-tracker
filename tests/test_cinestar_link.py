import datetime

from src.cinestar_link import build_cinestar_slug_candidates, resolve_cinestar_url


_RECENT_YEAR = datetime.datetime.now().year


def _page_html(year: int) -> str:
    """Minimal CineStar-film-page stub that contains the Produktionsjahr block."""
    return (
        "<html><body>"
        f"<b>Produktionsjahr</b><span>{year}</span>"
        "</body></html>"
    )


class _FakeResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


def test_build_cinestar_slug_candidates_tries_full_then_title_parts():
    assert build_cinestar_slug_candidates("Der Astronaut - Project Hail Mary") == [
        "der-astronaut-project-hail-mary",
        "der-astronaut",
        "project-hail-mary",
    ]


def test_build_cinestar_slug_candidates_adds_original_title_and_loose_umlaut_variant():
    assert build_cinestar_slug_candidates(
        "Für immer ein Teil von dir",
        "Reminders of Him",
    ) == [
        "fuer-immer-ein-teil-von-dir",
        "fur-immer-ein-teil-von-dir",
        "fuer-immer-ein-teil-von-dir-reminders-of-him",
        "fur-immer-ein-teil-von-dir-reminders-of-him",
        "reminders-of-him",
    ]


def test_resolve_cinestar_url_uses_matching_title_part_before_fallback(monkeypatch):
    requested_urls = []

    def fake_get(url, headers, timeout, allow_redirects):
        requested_urls.append(url)
        if url.endswith("/der-astronaut"):
            return _FakeResponse(200, _page_html(_RECENT_YEAR))
        return _FakeResponse(404)

    monkeypatch.setattr("src.cinestar_link.requests.get", fake_get)

    resolved = resolve_cinestar_url(
        "Der Astronaut - Project Hail Mary",
        "https://www.kinoprogramm.com/fallback",
    )

    assert resolved == "https://www.cinestar.de/kino-konstanz/film/der-astronaut"
    assert requested_urls == [
        "https://www.cinestar.de/kino-konstanz/film/der-astronaut-project-hail-mary",
        "https://www.cinestar.de/kino-konstanz/film/der-astronaut",
    ]


def test_resolve_cinestar_url_uses_original_title_combo_and_loose_slug(monkeypatch):
    requested_urls = []

    def fake_get(url, headers, timeout, allow_redirects):
        requested_urls.append(url)
        if url.endswith("/fur-immer-ein-teil-von-dir-reminders-of-him"):
            return _FakeResponse(200, _page_html(_RECENT_YEAR))
        return _FakeResponse(404)

    monkeypatch.setattr("src.cinestar_link.requests.get", fake_get)

    resolved = resolve_cinestar_url(
        "Für immer ein Teil von dir",
        "https://www.kinoprogramm.com/fallback",
        "Reminders of Him",
    )

    assert resolved == "https://www.cinestar.de/kino-konstanz/film/fur-immer-ein-teil-von-dir-reminders-of-him"
    assert requested_urls == [
        "https://www.cinestar.de/kino-konstanz/film/fuer-immer-ein-teil-von-dir",
        "https://www.cinestar.de/kino-konstanz/film/fur-immer-ein-teil-von-dir",
        "https://www.cinestar.de/kino-konstanz/film/fuer-immer-ein-teil-von-dir-reminders-of-him",
        "https://www.cinestar.de/kino-konstanz/film/fur-immer-ein-teil-von-dir-reminders-of-him",
    ]


def test_resolve_cinestar_url_rejects_zombie_page_when_year_mismatches(monkeypatch):
    """The /film/michael slug collides with a 2011 Austrian film page that
    is still live on CineStar. When we know the TMDb year of the film we
    mean (e.g. 2025), the old page must be rejected and we fall back to
    the kinoprogramm URL."""
    requested_urls = []

    def fake_get(url, headers, timeout, allow_redirects):
        requested_urls.append(url)
        # Every candidate returns 200, but the page is the zombie 2011 page.
        return _FakeResponse(200, _page_html(2011))

    monkeypatch.setattr("src.cinestar_link.requests.get", fake_get)

    resolved = resolve_cinestar_url(
        "Michael",
        "https://www.kinoprogramm.com/fallback",
        expected_year=2025,
    )

    assert resolved == "https://www.kinoprogramm.com/fallback"
    assert requested_urls == [
        "https://www.cinestar.de/kino-konstanz/film/michael",
    ]


def test_resolve_cinestar_url_rejects_old_page_without_expected_year(monkeypatch):
    """Without an expected year, a page whose Produktionsjahr is clearly
    old (more than ~4 years) is rejected to avoid zombie collisions."""

    def fake_get(url, headers, timeout, allow_redirects):
        return _FakeResponse(200, _page_html(2011))

    monkeypatch.setattr("src.cinestar_link.requests.get", fake_get)

    resolved = resolve_cinestar_url(
        "Michael",
        "https://www.kinoprogramm.com/fallback",
    )

    assert resolved == "https://www.kinoprogramm.com/fallback"
