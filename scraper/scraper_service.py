import sys
import os

# Aggiunge la root del repository al PYTHONPATH
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, repo_root)

print("Current working directory:", os.getcwd())  # Debugging
print("Updated sys.path:", sys.path)  # Debugging

from db.db_manager import DatabaseManager  # Ora dovrebbe funzionare
from scraper.parser import AlboParser
from scraper.telegram_notifier import TelegramNotifier


def job_monitor():
    db_manager = DatabaseManager()
    parser = AlboParser()
    notifier = TelegramNotifier()

    print("Esecuzione del job di monitoraggio...")
    pubblicazioni = parser.estrai_pubblicazioni()
    for pub in pubblicazioni:
        if not db_manager.pubblicazione_esiste(pub["numero_pubblicazione"]):
            db_manager.salva_pubblicazione(pub)
            notifier.invia_messaggio(pub)

if __name__ == "__main__":
    if "--once" in sys.argv:
        job_monitor()
    else:
        scheduler = BlockingScheduler()
        scheduler.add_job(job_monitor, 'interval', minutes=30)
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("Chiusura del servizio di scraping.")
