import time
import logging
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domashna1.pipeline.filter1_fetch_coins import Filter1FetchCoins
from domashna1.pipeline.filter2_check_last_date import Filter2FetchHistory
from domashna1.pipeline.filter3_fetch_missing_data import Filter3FillMissing

logger = logging.getLogger(__name__)

def run_pipeline():
    start = time.perf_counter()
    logger.info("=== PIPELINE ZAPOCNA ===")

    f1 = Filter1FetchCoins()
    t1 = time.perf_counter()
    coins = f1.process()
    logger.info(f"Cekor 1: Sobrani {len(coins)} coins vo {time.perf_counter() - t1:.2f}s")
    logger.info("====================================================\n\n\n\n\n")

    f2 = Filter2FetchHistory()
    t2 = time.perf_counter()
    coins_after_history = f2.process(coins)
    logger.info(f"Cekor 2: Proverka na history za {len(coins_after_history)} coins vo {time.perf_counter() - t2:.2f}s")
    logger.info("====================================================\n\n\n\n\n")

    f3 = Filter3FillMissing()
    t3 = time.perf_counter()
    coins_after_fill = f3.process(coins_after_history)
    logger.info(f"Cekor 3: Procesirani {len(coins_after_fill)} coins in {time.perf_counter() - t3:.2f}s")
    logger.info("====================================================\n\n")

    total_time = time.perf_counter() - start
    logger.info(f"Pipeline zavrsi uspesno za {total_time:.2f}s")
    logger.info(f"Coins posle sekoj cekor: F1={len(coins)}, F2={len(coins_after_history)}, F3={len(coins_after_fill)}")

if __name__ == "__main__":
    run_pipeline()
