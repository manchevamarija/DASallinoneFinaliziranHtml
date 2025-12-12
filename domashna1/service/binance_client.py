import json
import logging
import os
import time
from datetime import datetime
from typing import List, Dict, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BinanceClient:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.exchange_info_url = f"{self.base_url}/exchangeInfo"
        self.klines_url = f"{self.base_url}/klines"
        self.ticker_24h_url = f"{self.base_url}/ticker/24hr"
        self.cache_file = "binance_symbols.json"

        logger.info("Startuvam Binance client...")
        self.supported_pairs = self._load_supported_pairs()

    def _load_supported_pairs(self) -> set:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    symbols = set(json.load(f))
                logger.info(f"Cache najden — {len(symbols)} simboli vcitani.")
                return symbols
            except Exception as e:
                logger.warning(f"Problem so cache fajlot: {e} .")

        try:
            logger.info("Zemam lista na trading pairs od Binance...")
            res = requests.get(self.exchange_info_url, timeout=5)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            logger.error(f"Greska pri povlekuvanje na exchange info: {e}")
            return set()

        symbols = {s["symbol"] for s in data.get("symbols", [])}

        try:
            with open(self.cache_file, "w") as f:
                json.dump(list(symbols), f)
        except Exception as e:
            logger.warning(f"Ne moze da se zacuva cache: {e}")

        logger.info(f"Zacuvani {len(symbols)} simboli vo cache.")
        return symbols

    def is_supported(self, pair: str) -> bool:
        return pair in self.supported_pairs

    def fetch_ohlcv(self, symbol: str, start_date: datetime) -> List[dict]:
        if not self.is_supported(symbol):
            logger.info(f"{symbol} ne e podrzan par — skip.")
            return []

        interval = "1d"
        limit = 1000
        results = []

        start_ts = int(start_date.timestamp() * 1000)
        now_ts = int(time.time() * 1000)

        logger.info(f"{symbol}: Povlekuvam OHLCV podatoci od {start_date.date()}...")

        while start_ts < now_ts:
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "startTime": start_ts
            }

            try:
                r = requests.get(self.klines_url, params=params, timeout=7)
                r.raise_for_status()
            except Exception as e:
                logger.warning(f"{symbol}: greska pri  fetch: {e}")
                break

            data = r.json()
            if not data:
                break

            base_symbol = symbol.replace("USDT", "")

            for row in data:
                ts = row[0]
                date_str = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")

                results.append({
                    "symbol": base_symbol,
                    "date": date_str,
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5])
                })

            last_ts = data[-1][0]
            start_ts = last_ts + 86_400_000

            time.sleep(0.25)

        return results

    def fetch_daily_stats(self, symbol: str) -> Optional[Dict[str, float]]:
        if not self.is_supported(symbol):
            logger.info(f"{symbol} ne e vo lista na podrzani simboli.")
            return None

        try:
            r = requests.get(self.ticker_24h_url, params={"symbol": symbol}, timeout=5)
            r.raise_for_status()
        except Exception as e:
            logger.warning(f"{symbol}: neuspeshno prevzemanje na daily stats: {e}")
            return None

        d = r.json()
        return {
            "symbol": symbol,
            "last_price": float(d.get("lastPrice", 0)),
            "high_24h": float(d.get("highPrice", 0)),
            "low_24h": float(d.get("lowPrice", 0)),
            "volume_24h": float(d.get("volume", 0)),
            "liquidity": float(d.get("quoteVolume", 0)),
        }
