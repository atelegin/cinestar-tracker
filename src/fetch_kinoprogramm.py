import logging
import requests
import yaml
import time
import socket
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests.packages.urllib3.util.connection as urllib3_cn
from typing import Optional

# Force IPv4 to avoid "Network is unreachable" on GitHub Actions (IPv6 issues)
def allowed_gai_family():
    return socket.AF_INET

urllib3_cn.allowed_gai_family = allowed_gai_family

logger = logging.getLogger(__name__)


def _build_discovery_url(schedule_url: str) -> Optional[str]:
    """Build city-level URL from cinema schedule URL."""
    parsed = urlparse(schedule_url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 3 or parts[0] != "kino":
        return None
    city_slug = parts[1]
    return f"{parsed.scheme}://{parsed.netloc}/kino/{city_slug}"


def _discover_updated_cinema_url(
    original_url: str, headers: dict, timeout: int
) -> Optional[str]:
    """Try to find updated cinema link when old schedule URL returns 404."""
    parsed = urlparse(original_url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 3:
        return None

    city_slug = parts[1]
    cinema_slug = parts[2]
    discovery_url = _build_discovery_url(original_url)
    if not discovery_url:
        return None

    try:
        logger.info(f"Trying URL discovery via {discovery_url}")
        response = requests.get(discovery_url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"URL discovery request failed: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    prefix = f"/kino/{city_slug}/{cinema_slug}"

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith(prefix):
            return f"{parsed.scheme}://{parsed.netloc}{href}"
    return None

def load_settings(path: str = "config/settings.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def fetch_schedule_html() -> Optional[str]:
    settings = load_settings()
    url = settings["kinoprogramm_url"]
    current_url = url
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
            logger.info(f"Fetching {current_url}, attempt {attempt + 1}/{retries + 1}")
            response = requests.get(current_url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Request failed: {e}")
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code == 404 and current_url == url:
                discovered_url = _discover_updated_cinema_url(url, headers, timeout)
                if discovered_url and discovered_url != current_url:
                    logger.info(f"Discovered updated cinema URL: {discovered_url}")
                    current_url = discovered_url
                    continue
            if attempt < retries:
                time.sleep(2)  # Simple backoff
            else:
                logger.error("All retries exhausted.")
                return None
    return None
