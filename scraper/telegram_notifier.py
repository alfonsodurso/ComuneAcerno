import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEOUT

def escape_markdown(text):
    """Evita errori di formattazione in Markdown di Telegram."""
    if not isinstance(text, str):
        text = str(text)
    for ch in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(ch, f"\\{ch}")
    return text

class TelegramNotifier:
    def __init__(self, token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID):
        self.token = token
        self.chat_id = chat_id
        self.session = requests.Session()

    def invia_messaggio(self, pubblicazione):
        """Invia un messaggio Telegram con i dettagli della pubblicazione."""

        skip_keys = {
            "Tipo Atto",
            "Registro Generale",
            "Data Registro Generale",
            "Data Fine Pubblicazione"
        }

        # **Inizio Messaggio**
        lines = ["📢 *Nuova pubblicazione*\n"]

        # **Dati della pubblicazione**
        for key in sorted(pubblicazione.keys()):
            key_title = key.replace('_', ' ').title()
            if key_title in skip_keys:
                continue
            value = escape_markdown(pubblicazione[key])
            lines.append(f"📌 *{key_title}:* {value}")

        # **Documento principale**
        documento = pubblicazione.get("documento", "").strip()
        if documento:
            lines.append(f"\n📄 *Documento:* [Link al documento]({documento})")

        # **Allegati**
        allegati = pubblicazione.get("allegati", [])
        if allegati:
            allegati_links = "\n".join([f"🔗 [Link]({a})" for a in allegati])
            lines.append(f"\n📎 *Allegati:*\n{allegati_links}")

        # **Nota Finale**
        lines.append("\n⚠️ *Nota:* se il download non parte automaticamente, apri il link con il tuo browser.")

        # **Invio del messaggio**
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
