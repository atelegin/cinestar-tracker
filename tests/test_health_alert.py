from datetime import datetime, timedelta, timezone

import src.health_alert as ha
import src.state as st


def _setup(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "STATE_PATH", tmp_path / "state.json")
    sent = []
    monkeypatch.setattr(ha, "_send", lambda text: sent.append(text) or True)
    return sent


def test_alert_dedup_and_recovery(tmp_path, monkeypatch):
    sent = _setup(tmp_path, monkeypatch)
    t0 = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)

    ha.raise_alert("parser", "https://x", now=t0)
    ha.raise_alert("parser", "https://x", now=t0 + timedelta(hours=6))
    assert len(sent) == 1 and "вёрстку" in sent[0]

    ha.raise_alert("parser", "https://x", now=t0 + timedelta(hours=25))
    assert len(sent) == 2

    ha.clear_alerts(38)
    assert "снова видит" in sent[-1]
    assert st.load_state()["health_alerts"] == {}

    ha.clear_alerts(38)
    assert len(sent) == 3  # no repeat recovery message


def test_network_failure_waits_24h(tmp_path, monkeypatch):
    sent = _setup(tmp_path, monkeypatch)
    t0 = datetime(2026, 11, 14, 5, tzinfo=timezone.utc)
    ha.raise_alert("fetch", "u", now=t0)
    ha.raise_alert("fetch", "u", now=t0 + timedelta(hours=12))
    assert sent == []
    ha.raise_alert("fetch", "u", now=t0 + timedelta(hours=25))
    assert len(sent) == 1


def test_recovery_resets_network_timer_silently(tmp_path, monkeypatch):
    sent = _setup(tmp_path, monkeypatch)
    t0 = datetime(2026, 11, 14, 5, tzinfo=timezone.utc)
    ha.raise_alert("api", "u", now=t0)
    ha.clear_alerts(10)
    assert sent == []
    ha.raise_alert("api", "u", now=t0 + timedelta(hours=30))
    assert sent == []  # timer restarted, not 30h of continuous failure
