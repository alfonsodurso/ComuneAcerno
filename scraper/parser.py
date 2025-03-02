import re
import requests
from bs4 import BeautifulSoup
from config import BASE_URL, ALBO_URL, TIMEOUT

class AlboParser:
    def __init__(self):
        self.session = requests.Session()

    def estrai_dettagli(self, dettagli_link):
        dettagli = {}
        try:
            response = self.session.get(dettagli_link, timeout=TIMEOUT)
            response.raise_for_status()
        except Exception as e:
            print(f"Errore nel recupero di {dettagli_link}: {e}")
            return dettagli

        try:
            soup = BeautifulSoup(response.text, 'lxml')
        except Exception:
            soup = BeautifulSoup(response.text, 'html.parser')

        rows = soup.find_all("div", class_="row detail-row")
        for row in rows:
            label_div = row.find("div", class_="col-md-3 detail-label")
            value_div = row.find("div", class_="col-md-9 detail-value")
            if label_div and value_div:
                label_text = label_div.text.strip()
                if label_text.lower() in ["documento", "allegati"]:
                    continue
                dettagli[label_text] = value_div.text.strip()

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

    def estrai_pubblicazioni(self):
        try:
            response = self.session.get(ALBO_URL, timeout=TIMEOUT)
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
        rows = table.find_all("tr")[1:]  # salta l'intestazione
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 5:
                continue
            oggetto_link = cells[1].find("a")
            if oggetto_link and oggetto_link.has_attr("href"):
                dettagli_link = BASE_URL[:-1] + oggetto_link["href"]
            else:
                dettagli_link = "#"
            dettagli_pubblicazione = self.estrai_dettagli(dettagli_link)
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
