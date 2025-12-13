from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3, os

app = FastAPI()


app.mount("/static", StaticFiles(directory="domashna3/static"), name="static")
templates = Jinja2Templates(directory="domashna3/templates")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../domashna1/crypto.db")

def get_connection():
    return sqlite3.connect(DB_PATH)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/cryptos")
def show_cryptos(request: Request, filter_id: str = None, page: int = 1):
    limit = 20
    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coins';")
    if not cursor.fetchone():
        return templates.TemplateResponse("cryptos.html", {
            "request": request,
            "cryptos": [],
            "all_cryptos": [],
            "selected": None,
            "page": 1,
            "total_pages": 1,
            "error": "Табелата 'coins' не постои во базата."
        })

    cursor.execute("SELECT id, name FROM coins ORDER BY market_cap_rank LIMIT 200")
    all_cryptos = cursor.fetchall()

    if filter_id:
        cursor.execute("""
            SELECT id, symbol, name, market_cap, market_cap_rank
            FROM coins
            WHERE id = ?
        """, (filter_id,))
        rows = cursor.fetchall()
        total_pages = 1
    else:
        cursor.execute("SELECT COUNT(*) FROM coins")
        total = cursor.fetchone()[0]
        total_pages = (total // limit) + (1 if total % limit else 0)

        cursor.execute(f"""
            SELECT id, symbol, name, market_cap, market_cap_rank
            FROM coins
            ORDER BY market_cap_rank
            LIMIT {limit} OFFSET {offset}
        """)
        rows = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse("cryptos.html", {
        "request": request,
        "cryptos": rows,
        "all_cryptos": all_cryptos,
        "selected": filter_id,
        "page": page,
        "total_pages": total_pages
    })


@app.get("/za-nas")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/grafici")
def show_graphs(request: Request):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, market_cap
        FROM coins
        WHERE market_cap IS NOT NULL
        ORDER BY market_cap DESC
        LIMIT 10
    """)
    data = cursor.fetchall()
    conn.close()

    names = [row[0] for row in data]
    caps = [row[1] for row in data]

    return templates.TemplateResponse("grafici.html", {
        "request": request,
        "names": names,
        "caps": caps
    })
