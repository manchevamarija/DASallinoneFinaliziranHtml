import sqlite3
import logging
from typing import Optional, List, Tuple, Dict


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Database:

    def __init__(self, path: str = "crypto.db"):
        self.conn = sqlite3.connect(path)
        self.create_tables()

    def create_tables(self) -> None:

        try:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS coins (
                        id TEXT PRIMARY KEY,
                        symbol TEXT,
                        name TEXT,
                        market_cap REAL,
                        market_cap_rank INTEGER
                    )
                """)

                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT,
                        date TEXT,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL,
                        volume REAL
                    )
                """)

                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS daily_stats (
                        symbol TEXT PRIMARY KEY,
                        last_price REAL,
                        high_24h REAL,
                        low_24h REAL,
                        volume_24h REAL,
                        liquidity REAL
                    )
                """)

        except sqlite3.Error as err:
            logger.error(f"Ne uspeav da gi kreiram tabelite: {err}")

    def get_last_date(self, symbol: str) -> Optional[str]:

        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT MAX(date)
                FROM history
                WHERE symbol = ?
            """, (symbol,))

            row = cursor.fetchone()
            return row[0] if row and row[0] else None

        except sqlite3.Error as err:
            logger.error(f"Greska pri baranje posledna data za '{symbol}': {err}")
            return None

        finally:
            cursor.close()

    def insert_history_rows(self, rows: list[dict]) -> None:

        try:
            with self.conn:
                self.conn.executemany("""
                    INSERT OR REPLACE INTO history
                    (symbol, date, open, high, low, close, volume)
                    VALUES (:symbol, :date, :open, :high, :low, :close, :volume)
                """, rows)
        except sqlite3.Error as err:
            import logging
            logging.error(f"Greska pri vnesuvanje na history redovi: {err}")

    def save_daily_stats(self, stats: Dict[str, float]) -> None:

        try:
            with self.conn:
                self.conn.execute("""
                    INSERT OR REPLACE INTO daily_stats
                    (symbol, last_price, high_24h, low_24h, volume_24h, liquidity)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    stats["symbol"],
                    stats["last_price"],
                    stats["high_24h"],
                    stats["low_24h"],
                    stats["volume_24h"],
                    stats["liquidity"]
                ))

        except sqlite3.Error as err:
            logger.error(f"Greska pri cuvanje na daily stats za {stats.get('symbol')}: {err}")

    def close(self) -> None:

        try:
            self.conn.close()
        except sqlite3.Error as err:
            logger.error(f"Greska pri zatvoranje na bazata: {err}")
