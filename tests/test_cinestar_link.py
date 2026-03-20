from src.cinestar_link import build_cinestar_slug_candidates, resolve_cinestar_url


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

    class Response:
        def __init__(self, status_code: int):
            self.status_code = status_code

    def fake_head(url, headers, timeout, allow_redirects):
        requested_urls.append(url)
        if url.endswith("/der-astronaut"):
            return Response(200)
        return Response(404)

    monkeypatch.setattr("src.cinestar_link.requests.head", fake_head)

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

    class Response:
        def __init__(self, status_code: int):
            self.status_code = status_code

    def fake_head(url, headers, timeout, allow_redirects):
        requested_urls.append(url)
        if url.endswith("/fur-immer-ein-teil-von-dir-reminders-of-him"):
            return Response(200)
        return Response(404)

    monkeypatch.setattr("src.cinestar_link.requests.head", fake_head)

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
