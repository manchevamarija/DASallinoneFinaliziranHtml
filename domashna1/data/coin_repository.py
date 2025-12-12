from typing import List
from domashna1.data.db import Database
from domashna1.model.coin import Coin


class CoinRepository:

    def __init__(self):
        self.db = Database()

    def save_all(self, coins: List[Coin]) -> None:
        conn = self.db.conn
        cursor = conn.cursor()

        try:
            insert_sql = """
                INSERT OR REPLACE INTO coins (id, symbol, name, market_cap, market_cap_rank)
                VALUES (?, ?, ?, ?, ?)
            """

            coin_rows = [
                (c.id, c.symbol, c.name, c.market_cap, c.market_cap_rank)
                for c in coins
            ]

            cursor.executemany(insert_sql, coin_rows)
            conn.commit()

        except Exception as ex:
            print(f"[ERROR] Neuspesno zacuvuvanje na coins: {ex}")
            conn.rollback()

        finally:
            cursor.close()

    def get_all_symbols(self) -> List[Coin]:
        cursor = self.db.conn.cursor()

        try:
            cursor.execute("SELECT id, symbol, name FROM coins")
            rows = cursor.fetchall()

            return [Coin(id=r[0], symbol=r[1], name=r[2]) for r in rows]

        except Exception as ex:
            print(f"[ERROR] Ne mozam da gi povlecam simvolite od tabela coins: {ex}")
            return []

        finally:
            cursor.close()
