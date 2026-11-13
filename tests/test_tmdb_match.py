from src.tmdb_match import build_search_variants, normalize_title


def test_build_search_variants_tries_english_half_for_german_then_english_title():
    normalized = normalize_title("Der Astronaut - Project Hail Mary")

    assert build_search_variants(normalized) == [
        "Der Astronaut - Project Hail Mary",
        "Project Hail Mary",
    ]


def test_build_search_variants_keeps_english_half_for_english_then_german_title():
    normalized = normalize_title("The Housemaid - Wenn sie wüsste")

    assert build_search_variants(normalized) == [
        "The Housemaid - Wenn sie wüsste",
        "The Housemaid",
    ]


class _Resp:
    status_code = 200

    def __init__(self, results):
        self._r = results

    def json(self):
        return {"results": self._r}


def _fake_get(results):
    return lambda url, params=None, timeout=None: _Resp(results)


def test_dash_vs_endash_title_matches(monkeypatch):
    import datetime
    import src.tmdb_match as tm
    y = datetime.datetime.now().year
    monkeypatch.setattr(tm.requests, "get", _fake_get([
        {"id": 1300968, "title": "Die Tribute von Panem – Sunrise on the Reaping",
         "original_title": "The Hunger Games: Sunrise on the Reaping",
         "release_date": f"{y}-11-19", "vote_count": 10},
    ]))
    tid, reason = tm.tmdb_search("Die Tribute von Panem - Sunrise on the Reaping", api_key="k")
    assert tid == 1300968, reason


def test_same_title_prefers_current_year_release(monkeypatch):
    import datetime
    import src.tmdb_match as tm
    y = datetime.datetime.now().year
    monkeypatch.setattr(tm.requests, "get", _fake_get([
        {"id": 1291143, "title": "How to Rob a Bank", "original_title": "How to Rob a Bank",
         "release_date": f"{y-1}-03-05", "vote_count": 6000},
        {"id": 1437511, "title": "How to Rob a Bank", "original_title": "How to Rob a Bank",
         "release_date": f"{y}-11-13", "vote_count": 40},
    ]))
    tid, _ = tm.tmdb_search("How to Rob A Bank", api_key="k")
    assert tid == 1437511
