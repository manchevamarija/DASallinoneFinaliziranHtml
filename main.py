import os
import sqlite3

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), "crypto.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coins (
        id TEXT PRIMARY KEY,
        name TEXT,
        symbol TEXT,
        market_cap REAL,
        market_cap_rank INTEGER
    )
    """)
    conn.commit()
    conn.close()

init_db()
