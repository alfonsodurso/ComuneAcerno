import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEOUT

def escape_markdown(text):
    if not isinstance(text, str):
        text = str(text)
    # Escaping per Markdown
    for ch in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}']:
        text = text.replace(ch, f"\\{ch}")
    return text

class TelegramNotifier:
    def __init__(self, token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID):
        self.token = token
        self.chat_id = chat_id
        self.session = requests.Session()

    def invia_messaggio(self, pubblicazione):
        """Genera e invia il messaggio Telegram formattato."""
        
        # Definizione delle chiavi da escludere nel messaggio principale
        skip_keys = {
            "Tipo Atto",
            "Registro Generale",
            "Data Registro Generale",
            "Data Fine Pubblicazione",
            "Allegati"  # 🔹 Evita la ripetizione della lista iniziale degli allegati
        }

        lines = ["📢 *Nuova pubblicazione*\n"]  # Intestazione del messaggio

        # Generazione del corpo del messaggio
        for key in sorted(pubblicazione.keys()):
            key_title = key.replace('_', ' ').title()
            if key_title in skip_keys:
                continue  # Escludi le chiavi non necessarie
            value = escape_markdown(pubblicazione[key])
            lines.append(f"📌 *{key_title}:* {value}")

        # Aggiunta del link al documento principale
        documento = pubblicazione.get("documento")
        if documento:
            lines.append(f"\n📄 *Documento:* [Link al documento]({documento})")

        # Aggiunta degli allegati con formato corretto
        allegati = pubblicazione.get("allegati", [])
        if allegati:
            lines.append("\n📎 *Allegati:*")
            for a in allegati:
                lines.append(f"🔗 [Link]({a})")

        # Nota finale per il download
        lines.append("\n⚠️ *Nota:* se il download non parte automaticamente, apri il link con il tuo browser.")

        # Unione del messaggio in formato Markdown
        testo = "\n".join(lines)
        
        # Invio del messaggio Telegram
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
