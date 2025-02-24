import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import time

# Configurazione bot Telegram e URL
TELEGRAM_BOT_TOKEN = "6611531315:AAFjmQMJTnLvyqTY11zHu7MXVHi07llu-Rw"
TELEGRAM_CHAT_ID = "134014405"
BASE_URL = "https://www.halleyweb.com/c065001/mc/"
ALBO_URL = BASE_URL + "mc_p_ricerca.php?noHeaderFooter=1&multiente=c065001"
DB_NAME = "pubblicazioni.db"
TIMEOUT = 10  # secondi

# Sessione globale per le richieste HTTP (riutilizzo delle connessioni)
session = requests.Session()

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS pubblicazioni (
                numero_pubblicazione TEXT PRIMARY KEY,
                mittente TEXT,
                tipo_atto TEXT,
                registro_generale TEXT,
                data_registro_generale TEXT,
                oggetto_atto TEXT,
                data_inizio_pubblicazione TEXT,
                data_fine_pubblicazione TEXT,
                documento_principale TEXT,
                allegati TEXT
            )
        """)
        conn.commit()

def pubblicazione_esiste(numero_pubblicazione):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM pubblicazioni WHERE numero_pubblicazione = ?", (numero_pubblicazione,))
        return c.fetchone() is not None

def salva_pubblicazione(pubblicazione):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Assicurati che 'documento' sia una stringa (se è una lista, prendi il primo elemento)
        documento = pubblicazione["documento"]
        if isinstance(documento, list):
            documento = documento[0] if documento else "N/A"
        # Converte gli allegati in una stringa separata da virgola
        allegati = pubblicazione["allegati"]
        if isinstance(allegati, list):
            allegati = ",".join(allegati)
        c.execute("""
            INSERT OR IGNORE INTO pubblicazioni VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pubblicazione["numero_pubblicazione"],
            pubblicazione["mittente"],
            pubblicazione["tipo_atto"],
            pubblicazione["registro_generale"],
            pubblicazione["data_registro_generale"],
            pubblicazione["oggetto_atto"],
            pubblicazione["data_inizio_pubblicazione"],
            pubblicazione["data_fine_pubblicazione"],
            documento,
            allegati
        ))
        conn.commit()

def estrai_dettagli(dettagli_link):
    dettagli = {}
    try:
        response = session.get(dettagli_link, timeout=TIMEOUT)
        response.raise_for_status()
    except Exception as e:
        print(f"Errore nel recupero di {dettagli_link}: {e}")
        return dettagli

    # Usa "lxml" se disponibile per un parsing più veloce, altrimenti "html.parser"
    try:
        soup = BeautifulSoup(response.text, 'lxml')
    except Exception:
        soup = BeautifulSoup(response.text, 'html.parser')

    # Estrai i dettagli standard
    rows = soup.find_all("div", class_="row detail-row")
    for row in rows:
        label_div = row.find("div", class_="col-md-3 detail-label")
        value_div = row.find("div", class_="col-md-9 detail-value")
        if label_div and value_div:
            label_text = label_div.text.strip()
            # Escludi le etichette Documento e Allegati (vengono gestite separatamente)
            if label_text.lower() in ["documento", "allegati"]:
                continue
            dettagli[label_text] = value_div.text.strip()

    # Estrai documento principale e allegati dallo stesso soup
    allegati = []
    for link in soup.find_all("a", onclick=True):
        if "mc_attachment.php" in link["onclick"]:
            match = re.search(r"window\.open\('([^']+)'\)", link["onclick"])
            if match:
                allegati.append(BASE_URL + match.group(1))
    if allegati:
        dettagli["Documento"] = allegati[0]
        dettagli["Allegati"] = allegati[1:]
    else:
        dettagli["Documento"] = ""
        dettagli["Allegati"] = []
    
    return dettagli

def estrai_pubblicazioni():
    try:
        response = session.get(ALBO_URL, timeout=TIMEOUT)
        response.raise_for_status()
    except Exception as e:
        print("Errore nel recupero dell'Albo:", e)
        return []

    try:
        soup = BeautifulSoup(response.text, 'lxml')
    except Exception:
        soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table", {"id": "table-albo"})
    if not table:
        print("⚠️ Tabella delle pubblicazioni non trovata!")
        return []

    pubblicazioni = []
    rows = table.find_all("tr")[1:]  # Salta l'intestazione
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue
        oggetto_link = cells[1].find("a")
        if oggetto_link and oggetto_link.has_attr("href"):
            dettagli_link = BASE_URL[:-1] + oggetto_link["href"]
        else:
            dettagli_link = "#"
        dettagli_pubblicazione = estrai_dettagli(dettagli_link)
        pubblicazione = {
            "numero_pubblicazione": dettagli_pubblicazione.get("Numero pubblicazione", "N/A"),
            "mittente": dettagli_pubblicazione.get("Mittente", "N/A"),
            "tipo_atto": dettagli_pubblicazione.get("Tipo atto", "N/A"),
            "registro_generale": dettagli_pubblicazione.get("Registro generale", "N/A"),
            "data_registro_generale": dettagli_pubblicazione.get("Data registro generale", "N/A"),
            "oggetto_atto": dettagli_pubblicazione.get("Oggetto atto", "N/A"),
            "data_inizio_pubblicazione": dettagli_pubblicazione.get("Data inizio pubblicazione", "N/A"),
            "data_fine_pubblicazione": dettagli_pubblicazione.get("Data fine pubblicazione", "N/A"),
            "documento": dettagli_pubblicazione.get("Documento", "N/A"),
            "allegati": dettagli_pubblicazione.get("Allegati", [])
        }
        pubblicazioni.append(pubblicazione)
    
    return pubblicazioni

def escape_markdown(text):
    """Escapa i caratteri speciali per Telegram Markdown (MarkdownV1), salvo se il testo inizia con 'http'."""
    if not isinstance(text, str):
        text = str(text)
    if text.startswith("http"):
        return text
    for ch in ['_', '*', '[', ']', '(', ')']:
        text = text.replace(ch, f"\\{ch}")
    return text

def invia_messaggio_telegram(pubblicazione):
    lines = ["📌 *Nuova Pubblicazione Albo Pretorio*"]
    for key, value in pubblicazione.items():
        if key in ["documento", "allegati"]:
            continue
        lines.append(f"📄 *{key.replace('_', ' ').title()}:* {escape_markdown(value)}")
    
    # Campo documento
    documento = pubblicazione.get("documento")
    documento_str = f"[Link]({documento})" if documento else "Nessun documento"
    lines.append(f"📎 *Documento:* {documento_str}")
    
    # Campo allegati
    allegati = pubblicazione.get("allegati", [])
    if allegati:
        allegati_str = ", ".join(f"[Link]({a})" for a in allegati)
    else:
        allegati_str = "Nessun allegato"
    lines.append(f"📎 *Allegati:* {allegati_str}")
    
    testo = "\n".join(lines)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": testo,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = session.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Errore nell'invio del messaggio Telegram:", e)
        return {}

def monitora_albo():
    while True:
        for pub in estrai_pubblicazioni():
            if not pubblicazione_esiste(pub["numero_pubblicazione"]):
                salva_pubblicazione(pub)
                invia_messaggio_telegram(pub)
        time.sleep(3600)

if __name__ == "__main__":
    init_db()
    monitora_albo()
