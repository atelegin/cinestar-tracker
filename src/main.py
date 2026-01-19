import argparse
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="CineStar Konstanz OV Tracker")
    parser.add_argument("--dry-run", action="store_true", help="Print message instead of sending")
    parser.add_argument("--send", action="store_true", help="Send telegram message")
    parser.add_argument("--dump-missing", action="store_true", help="Print missing TMDb matches")
    parser.add_argument("--force", action="store_true", help="Force send even if week/hash matches (requires --send)")
    
    args = parser.parse_args()

    logger.info("Starting CineStar Tracker...")
    
    # --- PIPELINE START ---
    
    # 1. Fetch
    from src.fetch_kinoprogramm import fetch_schedule_html, load_settings
    html = fetch_schedule_html()
    if not html:
        logger.error("Failed to fetch HTML.")
        sys.exit(1)
        
    # 2. Parse
    from src.parse_schedule import parse_schedule
    settings = load_settings()
    
    sessions = parse_schedule(html, settings.get("timezone", "Europe/Berlin"))
    logger.info(f"Found {len(sessions)} total sessions.")
    
    # 3. Filter Week Window
    from src.week_interval import compute_week_window, filter_by_week
    from datetime import datetime, timedelta
    now = datetime.now()
    week_start, week_end = compute_week_window(now)
    week_start_str = week_start.strftime("%Y-%m-%d")
    logger.info(f"Week Window: {week_start.date()} to {week_end.date()}")
    
    sessions_in_window = filter_by_week(sessions, week_start, week_end)
    logger.info(f"Found {len(sessions_in_window)} sessions in window.")

    # 3b. Completeness Gate
    from src.week_completeness import is_week_complete
    
    # We check ALL sessions (not just filtered in window) or just sessions in window?
    # Actually, kinoprogramm logic is rolling. If we check 'sessions_in_window' for completeness, 
    # and the window is the target week, then max(sessions_in_window) tells us how far we have data FOR THAT WEEK.
    # However, if sessions_in_window is empty (early Monday), max() fails. 
    # Let's use `sessions` (all parsed) to determine horizon, but compare against week_end.
    
    is_complete = is_week_complete(sessions, week_start, week_end)
    
    max_dt = max(s.dt_local for s in sessions) if sessions else "None"
    required_wed = week_end - timedelta(days=1)
    
    logger.info(f"Completeness check: max_dt={max_dt}, required>={required_wed}. Complete={is_complete}")
    
    if not is_complete and not args.dry_run:
        logger.info("Week schedule incomplete (horizon too short). Skipping.")
        return

    # 4. Filter OV
    from src.ov_filter import filter_ov_sessions
    ov_sessions = filter_ov_sessions(sessions_in_window, settings.get("ov_markers", []))
    logger.info(f"Found {len(ov_sessions)} OV sessions in window.")
    
    # If NO OV sessions, we abort (do NOT update state used for weekly tracking)
    # UNLESS specifically debugging? No, rule is "Don't confirm empty week".
    if not ov_sessions and not args.dry_run:
        logger.info("No OV sessions found. Skipping update/send.")
        return

    # 5. Prepare Data (TMDb, CineStar Link, Selection)
    from src.tmdb_match import normalize_title, resolve_tmdb_id
    from src.cinestar_link import resolve_cinestar_url
    
    grouped = {}
    missing_titles = set()
    
    # Group
    for s in ov_sessions:
        norm = normalize_title(s.title)
        if norm not in grouped:
            grouped[norm] = []
        grouped[norm].append(s)
        
    final_items = []
    
    for norm_title, sessions_list in grouped.items():
        # Earliest session
        sessions_list.sort(key=lambda x: x.dt_local)
        earliest_session = sessions_list[0]
        
        # TMDb
        tmdb_id, _ = resolve_tmdb_id(norm_title)
        if not tmdb_id:
             missing_titles.add(norm_title)
             
        # Link
        c_url = resolve_cinestar_url(norm_title, earliest_session.film_url)
        
        final_items.append({
            'title': norm_title,
            'session': earliest_session,
            'tmdb_id': tmdb_id,
            'cinestar_url': c_url
        })
    
    final_items.sort(key=lambda x: x['session'].dt_local)
    
    # Format Message
    from src.format_message_ru import format_message
    msg_text = format_message(week_start, week_end, final_items)
    
    # --- PIPELINE END ---

    # Dry-run output
    if args.dry_run:
        print("\n--- Final Message Preview ---")
        print(msg_text)
        print("-----------------------------\n")
        
        if args.dump_missing:
            print("--- Missing Overrides Candidates (YAML) ---")
            for t in sorted(missing_titles):
                print(f'"{t}": # TODO_ID')
            print("-------------------------------------------\n")

    
    if args.send:
        logger.info("Send mode active.")
        
        # Load State
        from src.state import load_state as load_app_state, save_state as save_app_state, compute_content_hash
        import os
        
        state = load_app_state()
        last_start = state.get("last_sent_week_start")
        
        if last_start == week_start_str and not args.force:
            logger.info(f"Week {week_start_str} already sent. Skipping.")
            return

        # Prepare to send
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        if not token or not chat_id:
            logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")
            sys.exit(1)
            
        from src.telegram_send import send_message
        success = send_message(token, chat_id, msg_text)
        
        if success:
            state["last_sent_week_start"] = week_start_str
            state["last_hash"] = compute_content_hash(final_items)
            save_app_state(state)
            logger.info(f"State updated: Week {week_start_str} sent.")
        else:
            logger.error("Failed to send message. State NOT updated.")
            sys.exit(1)

if __name__ == "__main__":
    main()
