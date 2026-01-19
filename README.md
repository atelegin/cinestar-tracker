# CineStar Konstanz OV Tracker

A Telegram bot that monitors [CineStar Konstanz](https://www.kinoprogramm.com/kino/konstanz-universitaetsstadt/cinestar-konstanz-60996) for Original Version (OV/OmU) screenings and sends a weekly summary.

## Features
- **Smart Weekly Schedule**: Sends updates for the cinema week (Thu-Wed).
- **OV Filtering**: Strictly filters for OV, OmU, Originalfassung.
- **TMDb Integration**: Matches films to TMDb for Letterboxd links and metadata.
- **State Persistence**: Tracks sent weeks to prevent duplicates.
- **GitHub Actions**: Runs automatically every 6 hours.

## Deployment

### Prerequisites
1. Fork/Clone this repository.
2. In GitHub Repository -> Settings -> Secrets and variables -> Actions, add:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather.
   - `TELEGRAM_CHAT_ID`: Target chat ID (user or group).
   - `TMDB_API_KEY`: API Key from [themoviedb.org](https://www.themoviedb.org/).

### Workflow
The bot runs on a schedule (`0 */6 * * *` UTC).
- Checks for OV sessions for the *relevant* cinema week.
- If sessions found and not yet sent: Sends Telegram message and updates `state/state.json`.
- Commits `state/state.json` back to the repository.

## Local Usage
- **Smart Filtering**: Auto-detects OV/OmU screenings.
- **Weekly Summary**: Sends one post per cinema-week (Thursday-Wednesday).
- **Enriched Data**: Adds TMDb ratings and Letterboxd links if available.
- **Reliable**: Runs via GitHub Actions cron, with state persistence to avoid duplicates.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**:
   - `config/settings.yaml`: Main settings (URL, markers).
   - `config/overrides.yaml`: Manual mappings for TMDb IDs (`Title (Year)` -> `tmdb_id`).

3. **Running Locally**:
   ```bash
   # Check what would be sent without sending
   python -m src.main --dry-run
   
   # Send message (requires env vars)
   python -m src.main --send
   ```

## Secrets
For GitHub Actions or local sending, set these environment variables:
- `TELEGRAM_BOT_TOKEN`: Your bot token.
- `TELEGRAM_CHAT_ID`: Target chat ID.
- `TMDB_API_KEY`: (Optional) TMDb API key for better matching.
- `GH_PAT`: (CI Only) GitHub Personal Access Token with `contents: write` to commit state.
