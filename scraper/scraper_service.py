import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apscheduler.schedulers.blocking import BlockingScheduler
from db.db_manager import DatabaseManager
from scraper.parser import AlboParser
from scraper.telegram_notifier import TelegramNotifier

def job_monitor():
    db_manager = DatabaseManager()
    parser = AlboParser()
    notifier = TelegramNotifier()

    print("Esecuzione del job di monitoraggio...")
    pubblicazioni = parser.estrai_pubblicazioni()
    # Seleziona solo le pubblicazioni non ancora presenti nel DB
    new_pubs = [pub for pub in pubblicazioni if not db_manager.pubblicazione_esiste(pub["numero_pubblicazione"])]
    # Ordina in ordine crescente in base al numero pubblicazione
    try:
        new_pubs = sorted(new_pubs, key=lambda x: int(x["numero_pubblicazione"]))
    except ValueError:
        new_pubs = sorted(new_pubs, key=lambda x: x["numero_pubblicazione"])
    
    for pub in new_pubs:
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
