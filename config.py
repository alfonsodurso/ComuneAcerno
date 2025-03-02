import os

# Legge i valori dai Secrets di GitHub Actions
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

BASE_URL = "https://www.halleyweb.com/c065001/mc/"
ALBO_URL = BASE_URL + "mc_p_ricerca.php?noHeaderFooter=1&multiente=c065001"
DB_NAME = "pubblicazioni.db"
TIMEOUT = 10  # secondi
