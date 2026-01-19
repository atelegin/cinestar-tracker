import requests
import logging

logger = logging.getLogger(__name__)

def send_message(token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text
        # No parse_mode -> plain text
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        if not data.get("ok"):
            logger.error(f"Telegram API error: {data}")
            return False
            
        logger.info("Message sent successfully.")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False
