import logging
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from domashna1.data.db import Database
from domashna1.service.binance_client import BinanceClient
from domashna1.model.coin import Coin

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Filter2FetchHistory:


    def __init__(self, binance_client: BinanceClient = None):
        self.binance = binance_client if binance_client else BinanceClient()

    def _process_single_coin(self, coin: Coin) -> Dict[str, Any]:

        symbol = coin.symbol.upper()
        pair = f"{symbol}USDT"

        db = Database()

        try:
            if not self.binance.is_supported(pair):
                logger.info(f"[Filter2] {symbol}: Go preskoknuvam — {pair} ne e dostapen na Binance.")
                return {"symbol": symbol, "pair": pair, "ohlcv_count": 0, "daily_stats": None}

            last_date = db.get_last_date(symbol)

            if last_date is None:
                start_date = datetime.now() - timedelta(days=3650)
                logger.info(f"[Filter2] {symbol}: Nema prethodna istorija.")
            else:
                start_date = datetime.strptime(last_date, "%Y-%m-%d") + timedelta(days=1)
                logger.info(f"[Filter2] {symbol}: Prodolzuvam od {start_date.date()}.")

            rows = self.binance.fetch_ohlcv(pair, start_date)
            if rows:
                db.insert_history_rows(rows)

            stats = self.binance.fetch_daily_stats(pair)
            if stats:
                db.save_daily_stats(stats)

            return {
                "symbol": symbol,
                "pair": pair,
                "ohlcv_count": len(rows),
                "daily_stats": stats
            }

        except Exception as ex:
            logger.error(f"[Filter2] Greska pri obrabotka na {pair}: {ex}")
            return {"symbol": symbol, "pair": pair, "ohlcv_count": 0, "daily_stats": None}

        finally:
            db.close()

    def process(self, coins: List[Coin], max_workers: int = 20) -> List[Dict[str, Any]]:
        logger.info("=== Filter 2: Pocnuva paralelno povlekuvanje od Binance ===")
        start = time.perf_counter()

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            tasks = {
                pool.submit(self._process_single_coin, coin): coin.symbol.upper()
                for coin in coins
            }

            for future in as_completed(tasks):
                results.append(future.result())

        elapsed = time.perf_counter() - start
        logger.info(f"[TIMER] Filter 2 zavrsi za {elapsed:.2f}s (coins: {len(coins)})")
        logger.info("=== Filter 2: Zavrseno ===")

        return results
