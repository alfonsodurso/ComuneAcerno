import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEOUT

def escape_markdown(text):
    if not isinstance(text, str):
        text = str(text)
    if text.startswith("http"):
        return text
    for ch in ['_', '*', '[', ']', '(', ')']:
        text = text.replace(ch, f"\\{ch}")
    return text

class TelegramNotifier:
    def __init__(self, token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID):
        self.token = token
        self.chat_id = chat_id
        self.session = requests.Session()

    def invia_messaggio(self, pubblicazione):
        lines = ["📌 *Nuova Pubblicazione Albo Pretorio*"]
        for key, value in pubblicazione.items():
            if key in ["documento", "allegati"]:
                continue
            lines.append(f"📄 *{key.replace('_', ' ').title()}:* {escape_markdown(value)}")
        
        documento = pubblicazione.get("documento")
        documento_str = f"[Link]({documento})" if documento else "Nessun documento"
        lines.append(f"📎 *Documento:* {documento_str}")
        
        allegati = pubblicazione.get("allegati", [])
        allegati_str = ", ".join(f"[Link]({a})" for a in allegati) if allegati else "Nessun allegato"
        lines.append(f"📎 *Allegati:* {allegati_str}")
        
        testo = "\n".join(lines)
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": testo,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print("Errore nell'invio del messaggio Telegram:", e)
            return {}
