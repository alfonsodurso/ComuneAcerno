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
            "Allegati"  # Escludiamo la lista iniziale degli allegati
        }

        lines = ["📢 *Nuova pubblicazione*\n"]

        # Corpo del messaggio (escludendo alcune chiavi)
        for key in sorted(pubblicazione.keys()):
            key_title = key.replace('_', ' ').title()
            if key_title in skip_keys:
                continue
            value = escape_markdown(pubblicazione[key])
            lines.append(f"*{key_title}:* {value}")

        # Aggiunta del link al documento principale (si assume sia un solo link)
        documento = pubblicazione.get("documento")
        if documento and documento != "N/A":
            if isinstance(documento, list):
                doc_link = documento[0] if documento else ""
            else:
                doc_link = documento
            lines.append(f"\n*Documento:* [{doc_link}]({doc_link})")

        # Aggiunta degli allegati: ogni link su una riga separata
        allegati = pubblicazione.get("allegati")
        if allegati and allegati != "N/A":
            if isinstance(allegati, list):
                allegati_links = allegati
            else:
                allegati_links = [link.strip() for link in allegati.split(",") if link.strip()]
            if allegati_links:
                lines.append("\n*Allegati:*")
                for a in allegati_links:
                    lines.append(f"[{a}]({a})")

        # Nota per il download
        lines.append("\n⚠️ *Nota:* se il download non parte automaticamente, apri il link con il tuo browser.")

        # Nota per streamlit
        lines.append("\n🔎 *Vai su https://acerno.streamlit.app/ per maggiori informazioni.")
        
        # Composizione del messaggio in formato Markdown
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
