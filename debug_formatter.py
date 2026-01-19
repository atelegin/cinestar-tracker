
import os
import sys
from datetime import datetime, timedelta
from src.format_message_ru import format_message
from src.telegram_send import send_message
from src.parse_schedule import Session

def main():
    print("Preparing test message...")

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        sys.exit(1)

    # Mock week
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())  # Last Monday
    week_end = week_start + timedelta(days=7)

    # Mock items
    # Item 1: Full info
    s1 = Session("Iron Man (OV)", datetime.now() + timedelta(days=1, hours=2), "http://test.url", "OV")
    item1 = {
        "title": "Iron Man",
        "session": s1,
        "tmdb_id": 1726, # Iron Man
        "cinestar_url": "https://www.cinestar.de/test"
    }

    # Item 2: No TMDb
    s2 = Session("Unknown Movie (OV)", datetime.now() + timedelta(days=2, hours=4), "http://test.url", "OV")
    item2 = {
        "title": "Unknown Movie",
        "session": s2,
        "tmdb_id": None,
        "cinestar_url": "https://www.cinestar.de/test2"
    }

    # Item 3: No CineStar URL (fallback)
    s3 = Session("Fallback Movie (OV)", datetime.now() + timedelta(days=3, hours=5), "http://fallback.url", "OV")
    item3 = {
        "title": "Fallback Movie",
        "session": s3,
        "tmdb_id": 550, # Fight Club
        "cinestar_url": None
    }
    
    items = [item1, item2, item3]

    msg = format_message(week_start, week_end, items)
    print("--- Generated Message ---")
    print(msg)
    print("-----------------------")

    print(f"Sending to chat_id={chat_id}...")
    try:
        send_message(token, chat_id, msg)
        print("Success!")
    except Exception as e:
        print(f"Failed to send: {e}")

if __name__ == "__main__":
    main()
