import logging
from datetime import datetime, time as dt_time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from domashna1.data.db import Database
from domashna1.service.binance_client import BinanceClient
from domashna1.model.coin import Coin

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Filter3FillMissing:
    def __init__(self, binance_client: BinanceClient = None):
        self.binance = binance_client if binance_client else BinanceClient()

    def _process_single(self, coin: Coin) -> Dict[str, Any]:
        db = Database()
        symbol = coin.symbol.upper()
        pair = f"{symbol}USDT"

        try:
            if not self.binance.is_supported(pair):
                logger.info(f"[Filter3] {symbol}: Go skokam — {pair} ne go poddrzava Binance.")
                return {"coin": symbol, "added": 0}

            last_date = db.get_last_date(pair)
            if last_date is None:
                logger.info(f"[Filter3] {symbol}: Nema prethodni podatoci — skokni.")
                return {"coin": symbol, "added": 0}

            start_dt = datetime.combine(last_date, dt_time.min)
            end_dt = datetime.utcnow()

            if start_dt >= end_dt:
                logger.info(f"[Filter3] {symbol}: Nema novi podatoci.")
                return {"coin": symbol, "added": 0}

            logger.info(f"[Filter3] {symbol}: Povlekuvam podatoci od {start_dt.date()} do {end_dt.date()}.")

            ohlcv = self.binance.fetch_ohlcv(pair, start_dt)
            if not ohlcv:
                logger.info(f"[Filter3] {symbol}: Nema novi zapisi.")
                return {"coin": symbol, "added": 0}

            db.save_history_batch(pair, ohlcv)
            logger.info(f"[Filter3] {symbol}: Zacuvav {len(ohlcv)} novi redovi.")
            return {"coin": symbol, "added": len(ohlcv)}

        except Exception as e:
            logger.error(f"[Filter3] Greska pri obrabotka na {symbol}: {e}")
            return {"coin": symbol, "added": 0}

        finally:
            db.close()

    def process(self, coins: List[Coin], max_workers: int = 20) -> List[Dict[str, Any]]:
        from domashna1.model.coin import Coin
        coins = [Coin(symbol=c["symbol"], id=None, name=None, market_cap=None, market_cap_rank=None) if isinstance(c, dict) else c for c in coins]

        logger.info("=== Filter 3: Startuvam paralelna obrabotka za missing data ===")
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._process_single, coin): coin for coin in coins}

            for future in as_completed(futures):
                coin = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"[Filter3] Neuspesna obrabotka za {getattr(coin, 'symbol', coin)}: {e}")

        logger.info("=== Filter 3: Zavrseni site coins ===")
        return results
