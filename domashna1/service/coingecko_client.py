import logging
import time
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoinGeckoClient:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def get_top_coins(self, per_page: int = 250, pages: int = 4) -> List[Dict[str, Any]]:

        all_coins = []

        for page in range(1, pages + 1):
            url = (
                f"{self.BASE_URL}/coins/markets"
                f"?vs_currency=usd&order=market_cap_desc"
                f"&per_page={per_page}&page={page}&sparkline=false"
            )

            try:
                logger.info(f"[CoinGecko] Stranica {page}: povlekuvam top coins...")
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                coins = response.json()
                all_coins.extend(coins)
                time.sleep(1)
            except Exception as e:
                logger.warning(f"[CoinGecko] Ne uspеa da se zeme stranica {page}: {e}")
                continue

        logger.info(f"[CoinGecko] Vkupno povlecheni coins: {len(all_coins)}")
        return all_coins

    def fetch_daily_data(self, coin_id: str, start_date: datetime) -> List[Dict[str, Any]]:

        url = f"{self.BASE_URL}/coins/{coin_id}/market_chart?vs_currency=usd&days=max"

        try:
            logger.info(f"[CoinGecko] {coin_id}: povlekuvam dnevni podatoci...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning(f"[CoinGecko] {coin_id}: ne moze da se zeme istorija: {e}")
            return []

        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])

        if not prices:
            logger.info(f"[CoinGecko] {coin_id}: nema podatoci za ceni.")
            return []

        rows = []

        for i, (timestamp, price) in enumerate(prices):
            date = datetime.utcfromtimestamp(timestamp / 1000).date()
            if date < start_date.date():
                continue

            volume = volumes[i][1] if i < len(volumes) else None

            rows.append({
                "coin_id": coin_id,
                "date": str(date),
                "price": float(price),
                "volume": float(volume) if volume is not None else None
            })

        logger.info(f"[CoinGecko] {coin_id}: najdeni {len(rows)} zapisi po {start_date.date()}")
        return rows
