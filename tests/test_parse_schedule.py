from src.parse_schedule import parse_schedule
from src.ov_filter import filter_ov_sessions

HTML = """
<article class="kino-week-film" data-kino-week-film id="film-1">
  <a class="kino-week-poster" href="/kino/x/cinestar-konstanz/film-1"><img alt="poster"></a>
  <div><a class="text-lg" href="/kino/x/cinestar-konstanz/film-1">Love Story</a></div>
  <div class="kino-week-days">
    <section class="kino-week-day" data-kino-week-day="2026-11-19">
      <div data-kino-week-version="deutsch"><p>Deutsch</p>
        <span class="kino-week-time">16:45</span><span class="kino-week-time">20:00</span></div>
      <div data-kino-week-version="original-mit-untertiteln"><p>Original mit Untertiteln</p>
        <span class="kino-week-time">19:30</span></div>
    </section>
  </div>
</article>
"""

MARKERS = ["OV", "OmU", "Originalfassung", "Original mit Untertiteln"]


def test_parses_new_layout():
    sessions = parse_schedule(HTML)
    assert len(sessions) == 3
    s = sessions[0]
    assert s.title == "Love Story"
    assert s.film_url == "https://www.kinoprogramm.com/kino/x/cinestar-konstanz/film-1"
    assert s.dt_local.strftime("%Y-%m-%d %H:%M") == "2026-11-19 16:45"


def test_ov_filter_uses_version_not_title():
    ov = filter_ov_sessions(parse_schedule(HTML), MARKERS)
    assert [s.dt_local.strftime("%H:%M") for s in ov] == ["19:30"]
