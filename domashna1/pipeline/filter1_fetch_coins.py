import logging
from typing import List, Optional

from domashna1.pipeline.filter_base import Filter
from domashna1.service.coingecko_client import CoinGeckoClient
from domashna1.model.coin import Coin
from domashna1.data.coin_repository import CoinRepository

logger = logging.getLogger(__name__)


class Filter1FetchCoins(Filter):
    def __init__(
        self,
        client: Optional[CoinGeckoClient] = None,
        repository: Optional[CoinRepository] = None
    ):

        self.client = client if client else CoinGeckoClient()
        self.repository = repository if repository else CoinRepository()

    def process(self, data: Optional[dict] = None) -> List[Coin]:
        logger.info("Zapocnuvam so prevzemanje na top coins od CoinGecko...")

        try:
            raw_coins = self.client.get_top_coins()
        except Exception as e:
            logger.exception("Neuspesno prevzemanje od CoinGecko.")
            return []

        coins = []

        for c in raw_coins:
            if not c.get("market_cap"):
                continue

            try:
                coin = Coin(
                    id=c["id"],
                    symbol=c["symbol"],
                    name=c["name"],
                    market_cap=c["market_cap"],
                    market_cap_rank=c.get("market_cap_rank")
                )
                coins.append(coin)
            except KeyError as err:
                logger.warning(f"Preskoknat coin poradi nedostapni podatoci: {err}")

        logger.info(f"Prevzemeni {len(coins)} validni coins.")

        try:
            self.repository.save_all(coins)
        except Exception as e:
            logger.error(f"Greska pri zacuvuvanje vo baza: {e}")
        else:
            logger.info("Coins uspesno zacuvani vo bazata.")

        return coins
