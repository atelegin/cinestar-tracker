from src.fetch_cinestar import parse_shows, clean_title, version_label
from src.ov_filter import filter_ov_sessions

SHOWS = [
    {"_type": "movie", "movie": 1, "title": "Die Tribute von Panem - Sunrise on the Reaping",
     "detailLink": "/kino-konstanz/film/panem",
     "showtimes": [
         {"datetime": "2026-11-19 16:45 CET", "attributes": ["2D", "LANG_DE"]},
         {"datetime": "2026-11-19 19:30 CET", "attributes": ["AUDIO_OV", "LANG_EN", "OV"]},
     ]},
    {"_type": "event", "movie": 1, "title": "Preview: Tribute von Panem - Sunrise on the Reaping",
     "detailLink": "/kino-konstanz/veranstaltung-preview-panem",
     "showtimes": [{"datetime": "2026-11-18 19:30 CET", "attributes": ["AUDIO_OV", "OV"]}]},
    {"_type": "event", "movie": 2, "title": "Preview: You Can See Everything (OmU)",
     "detailLink": "/kino-konstanz/veranstaltung-preview-you-can-see-everything-omu",
     "showtimes": [{"datetime": "2026-11-19 19:00 CET",
                    "attributes": ["AUDIO_OmU", "LANG_EN", "OMU", "OV", "SUBS"]}]},
]

MARKERS = ["OV", "OmU", "Originalfassung"]


def test_preview_omu_event_is_found():
    ov = filter_ov_sessions(parse_shows(SHOWS), MARKERS)
    titles = {(s.title, s.tags, s.dt_local.strftime("%d.%m %H:%M")) for s in ov}
    assert ("You Can See Everything", "OmU", "19.11 19:00") in titles
    assert ("Die Tribute von Panem - Sunrise on the Reaping", "OV", "18.11 19:30") in titles
    assert len(ov) == 3  # dubbed 16:45 excluded


def test_event_url_is_absolute():
    s = [x for x in parse_shows(SHOWS) if x.title == "You Can See Everything"][0]
    assert s.film_url.startswith("https://www.cinestar.de/kino-konstanz/veranstaltung-")
    assert s.kind == "event"


def test_helpers():
    assert clean_title("Puella Magi Madoka Magica -Walpurgisnacht: Rising (jap.OmU) - Anime Nights 2026") \
        == "Puella Magi Madoka Magica -Walpurgisnacht: Rising"
    assert version_label(["LANG_DE", "FSK_12"]) == "Deutsch"
    assert version_label(["AUDIO_OV"]) == "OV"
