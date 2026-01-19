import logging
import requests
import yaml
import time
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
from typing import Optional

# Force IPv4 to avoid "Network is unreachable" on GitHub Actions (IPv6 issues)
def allowed_gai_family():
    return socket.AF_INET

urllib3_cn.allowed_gai_family = allowed_gai_family

logger = logging.getLogger(__name__)

def load_settings(path: str = "config/settings.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def fetch_schedule_html() -> Optional[str]:
    settings = load_settings()
    url = settings["kinoprogramm_url"]
    timeout = settings.get("request_timeout", 30)
    retries = settings.get("request_retries", 3)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
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
