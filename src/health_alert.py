"""Telegram alerts when the bot itself breaks (fetch failure, layout change).

Alerts are deduplicated via state["health_alerts"] so a broken parser sends
one message per day, not one every 6 hours. When things recover, a single
"back to normal" message is sent and the alert is cleared.
"""
import logging
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

REPEAT_AFTER = timedelta(hours=24)

# The runner is a laptop that can sleep (and lose network) at any moment, so
# network-type failures alert only if they persist this long. A parser break
# (page loaded fine, 0 sessions) alerts immediately.
NETWORK_KINDS = {"api", "fetch"}
PERSIST_BEFORE_ALERT = timedelta(hours=24)

MESSAGES = {
    "api": (
        "⚠️ CineStar-бот: API cinestar.de не отдал сеансы — временно беру данные "
        "с kinoprogramm.com (там нет превью и спецпоказов).\n"
        "{url}"
    ),
    "parser": (
        "⚠️ CineStar-бот: на странице kinoprogramm.com не найдено ни одного сеанса.\n"
        "Скорее всего, сайт снова поменял вёрстку — парсер нужно обновить.\n"
        "{url}"
    ),
    "fetch": (
        "⚠️ CineStar-бот: не удалось загрузить страницу kinoprogramm.com.\n"
        "{url}"
    ),
}

RECOVERY = "✅ CineStar-бот снова видит расписание ({count} сеансов)."


def _send(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.error("Cannot send health alert: Telegram credentials missing.")
        return False
    from src.telegram_send import send_message
    try:
        send_message(token, chat_id, text)
        return True
    except Exception as e:
        logger.error(f"Health alert send failed: {e}")
        return False


def raise_alert(kind: str, url: str = "", now: datetime | None = None) -> None:
    from src.state import load_state, save_state

    now = now or datetime.now(timezone.utc)
    state = load_state()

    since = state.get("health_failures_since") or {}
    if kind not in since:
        since[kind] = now.isoformat()
        state["health_failures_since"] = since
        save_state(state)
    if kind in NETWORK_KINDS:
        try:
            first = datetime.fromisoformat(since[kind])
        except ValueError:
            first = now
        if now - first < PERSIST_BEFORE_ALERT:
            logger.info(f"'{kind}' failing since {since[kind]}; not alerting yet (laptop may be asleep/offline).")
            return

    alerts = state.get("health_alerts") or {}
    last = alerts.get(kind)
    if last:
        try:
            if now - datetime.fromisoformat(last) < REPEAT_AFTER:
                logger.info(f"Health alert '{kind}' already sent at {last}; not repeating yet.")
                return
        except ValueError:
            pass

    text = MESSAGES[kind].format(url=url).strip()
    if _send(text):
        alerts[kind] = now.isoformat()
        state["health_alerts"] = alerts
        save_state(state)
        logger.info(f"Health alert '{kind}' sent.")


def clear_alerts(session_count: int) -> None:
    from src.state import load_state, save_state

    state = load_state()
    if state.get("health_failures_since"):
        state["health_failures_since"] = {}
        save_state(state)
    if not state.get("health_alerts"):
        return
    if _send(RECOVERY.format(count=session_count)):
        state["health_alerts"] = {}
        save_state(state)
        logger.info("Health alerts cleared (recovered).")
