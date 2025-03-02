import sys
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
