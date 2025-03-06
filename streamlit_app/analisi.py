import requests from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEOUT

def escape_markdown(text): if not isinstance(text, str): text = str(text) # Escaping base per Markdown for ch in ['_', '*', '[', ']', '(', ')']: text = text.replace(ch, f"\{ch}") return text

class TelegramNotifier: def init(self, token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID): self.token = token self.chat_id = chat_id self.session = requests.Session()

def invia_messaggio(self, pubblicazione):
    # Definisce le chiavi da escludere dal messaggio
    skip_keys = {
        "Tipo Atto",
        "Registro Generale",
        "Data Registro Generale",
        "Data Fine Pubblicazione"
    }
    lines = []
    # Invia le informazioni degli altri campi in ordine alfabetico
    for key in sorted(pubblicazione.keys()):
        key_title = key.replace('_', ' ').title()
        if key_title in skip_keys:
            continue
        value = pubblicazione[key]
        lines.append(f"{key_title}: {escape_markdown(value)}")
    
    # Aggiunge il link al documento (se presente)
    documento = pubblicazione.get("documento")
    if documento:
        documento_str = f"[Link al documento]({documento})"
    else:
        documento_str = "Nessun documento"
    lines.append(f"Documento: {documento_str}")
    
    # Aggiunge i link agli allegati (se presenti)
    allegati = pubblicazione.get("allegati", [])
    if allegati:
        allegati_str = ", ".join(f"[Link]({a})" for a in allegati)
    else:
        allegati_str = "Nessun allegato"
    lines.append(f"Allegati: {allegati_str}")
    
    # Nota per dispositivi mobili
    lines.append("Nota: se il download non parte automaticamente, apri il link con il tuo browser.")
    
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

Riscrivimi direttamente questo file per piacere con le modifiche fatte

