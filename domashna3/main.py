from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3

app = FastAPI()

app.mount("/static", StaticFiles(directory="domashna3/static"), name="static")
templates = Jinja2Templates(directory="domashna3/templates")

DB_PATH = "domashna1/crypto.db"

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/cryptos")
def show_cryptos(request: Request, filter_id: str = None, page: int = 1):
    limit = 20
    offset = (page - 1) * limit

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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

        cursor.execute("""
            SELECT id, symbol, name, market_cap, market_cap_rank
            FROM coins
            ORDER BY market_cap_rank
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        "cryptos.html",
        {
            "request": request,
            "cryptos": rows,
            "all_cryptos": all_cryptos,
            "selected": filter_id,
            "page": page,
            "total_pages": total_pages
        }
    )


@app.get("/za-nas")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/grafici")
def show_graphs(request: Request):
    conn = sqlite3.connect(DB_PATH)
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

    return templates.TemplateResponse(
        "grafici.html",
        {"request": request, "names": names, "caps": caps}
    )


@app.get("/lstm")
def lstm(request: Request):
    return templates.TemplateResponse(
        "lstm.html",
        {
            "request": request,
            "dates": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "true_prices": [30000, 30500, 31000],
            "predicted_prices": [29950, 30600, 30950],
        }
    )
