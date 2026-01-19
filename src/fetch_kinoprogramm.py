import logging
import requests
import yaml
import time
from typing import Optional

logger = logging.getLogger(__name__)

def load_settings(path: str = "config/settings.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def fetch_schedule_html() -> Optional[str]:
    settings = load_settings()
    url = settings["kinoprogramm_url"]
    timeout = settings.get("request_timeout", 15)
    retries = settings.get("request_retries", 1)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    for attempt in range(retries + 1):
        try:
            logger.info(f"Fetching {url}, attempt {attempt + 1}/{retries + 1}")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Request failed: {e}")
            if attempt < retries:
                time.sleep(2)  # Simple backoff
            else:
                logger.error("All retries exhausted.")
                return None
    return None
