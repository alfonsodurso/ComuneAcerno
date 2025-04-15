import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEOUT

def escape_markdown(text):
    """Escape minimo: scappa solo i caratteri che causano errori in Markdown."""
    if not isinstance(text, str):
        text = str(text)
    
    # Lista minima dei caratteri da scappare
    minimal_chars = ['_', '*', '[', ']', '(', ')']
    for ch in minimal_chars:
        text = text.replace(ch, f"\\{ch}")
    
    return text

class TelegramNotifier:
    def __init__(self, token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID):
        self.token = token
        self.chat_id = chat_id
        self.session = requests.Session()

    def invia_messaggio(self, pubblicazione):
        """Genera e invia il messaggio Telegram formattato."""
        
        # Chiavi da escludere dalla pubblicazione
        skip_keys = {
            "Tipo Atto", "Registro Generale", "Data Registro Generale",
            "Data Fine Pubblicazione", "Allegati", "Documento"
        }

        lines = ["📢 *Nuova pubblicazione*\n"]

        # Creazione del corpo del messaggio
        for key in sorted(pubblicazione.keys()):
            key_title = key.replace('_', ' ').title()
            if key_title in skip_keys:
                continue
            
            value = escape_markdown(pubblicazione[key])
            lines.append(f"*{key_title}:* {value}")

        # Link al documento principale
        documento = pubblicazione.get("documento")
        if documento and documento != "N/A":
            doc_link = documento[0] if isinstance(documento, list) else documento
            lines.append(f"\n*Documento:* [Apri]({doc_link})")

        # Aggiunta degli allegati (tutti su una riga)
        allegati = pubblicazione.get("allegati")
        if allegati and allegati != "N/A":
            allegati_links = allegati if isinstance(allegati, list) else [
                link.strip() for link in allegati.split(",") if link.strip()
            ]
            if allegati_links:
                allegati_formattati = " ".join(f"[Apri {i+1}]({a})" for i, a in enumerate(allegati_links))
                lines.append(f"*Allegati:* {allegati_formattati}")

        # Nota finale
        lines.append("\n⚠️ *Nota:* Se il download non parte automaticamente, apri il link con il tuo browser.")
        lines.append("\n🔎 Clicca [QUI](https://acerno.streamlit.app/) per maggiori informazioni.")

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
