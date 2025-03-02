import sqlite3
from config import DB_NAME

class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
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

    def pubblicazione_esiste(self, numero_pubblicazione):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM pubblicazioni WHERE numero_pubblicazione = ?", (numero_pubblicazione,))
            return c.fetchone() is not None

    def salva_pubblicazione(self, pubblicazione):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            documento = pubblicazione["documento"]
            if isinstance(documento, list):
                documento = documento[0] if documento else "N/A"
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

    def get_pubblicazioni(self):
        with sqlite3.connect(self.db_name) as conn:
            query = "SELECT * FROM pubblicazioni"
            data = conn.execute(query).fetchall()
        return data
