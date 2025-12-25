import requests
import pandas as pd
from pytrends.request import TrendReq
from transformers import pipeline

sentiment_model = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    framework="pt",
    device=-1
)

def get_hashrate():
    try:
        r = requests.get("https://api.blockchain.info/charts/hash-rate?timespan=30days&format=json").json()
        return r["values"][-1]["y"]
    except:
        return 0

def get_active_addresses():
    try:
        r = requests.get("https://api.blockchain.info/charts/n-unique-addresses?timespan=30days&format=json").json()
        return r["values"][-1]["y"]
    except:
        return 0

def get_tx_count():
    try:
        r = requests.get("https://api.blockchain.info/charts/n-transactions?timespan=30days&format=json").json()
        return r["values"][-1]["y"]
    except:
        return 0

def get_mvrv():
    try:
        r = requests.get("https://api.blockchain.info/charts/market-price?timespan=30days&format=json").json()
        market_price = r["values"][-1]["y"]
        r2 = requests.get("https://api.blockchain.info/charts/cost-per-transaction?timespan=30days&format=json").json()
        realized_price = r2["values"][-1]["y"]
        return market_price / realized_price if realized_price else 0
    except:
        return 0

def get_tvl():
    try:
        r = requests.get("https://api.llama.fi/charts/bitcoin").json()
        return r[-1]["totalLiquidityUSD"]
    except:
        return 0

def get_whale_alert():
    try:
        r = requests.get(
            "https://api.whale-alert.io/v1/transactions?api_key=demo&min_value=5000000"
        ).json()
        return len(r.get("transactions", []))
    except:
        return 0

def get_nvt():
    try:
        price = requests.get("https://api.blockchain.info/ticker").json()["USD"]["last"]
        vol = requests.get("https://api.blockchain.info/charts/output-volume?timespan=7days&format=json").json()
        volume = vol["values"][-1]["y"]
        return price / volume if volume else 0
    except:
        return 0

def get_reddit_sentiment():
    try:
        r = requests.get(
            "https://api.pushshift.io/reddit/search/submission/?subreddit=Bitcoin&size=20"
        ).json()

        titles = [p.get("title", "") for p in r.get("data", [])]
        if not titles:
            return 0

        score = 0
        for t in titles:
            label = sentiment_model(t)[0]["label"]
            score += 1 if label == "POSITIVE" else -1
        return score
    except:
        return 0


def get_news_sentiment():
    try:
        r = requests.get(
            "https://cryptopanic.com/api/v1/posts/?auth_token=demo&currencies=BTC"
        ).json()

        titles = [i["title"] for i in r.get("results", [])]
        if not titles:
            raise Exception("CryptoPanic empty")
    except:
        try:
            import feedparser
        except ImportError:
            return 0
        feed = feedparser.parse("https://www.coindesk.com/arc/outboundfeeds/rss/")
        titles = [e.title for e in feed.entries[:15]]
    if not titles:
        return 0
    score = 0
    for t in titles:
        label = sentiment_model(t)[0]["label"]
        score += 1 if label == "POSITIVE" else -1
    return score

def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1&format=json").json()
        return int(r["data"][0]["value"])
    except:
        return 0

def get_google_trends():
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload(["Bitcoin"], timeframe="now 7-d")
        data = pytrends.interest_over_time()
        return int(data["Bitcoin"].iloc[-1])
    except:
        return 0

def analyze_onchain():
    return {
        "hashrate": get_hashrate(),
        "active_addresses": get_active_addresses(),
        "transaction_count": get_tx_count(),
        "tvl": get_tvl(),
        "whale_movements": get_whale_alert(),
        "nvt": get_nvt(),
        "mvrv": get_mvrv()
    }

def analyze_sentiment():
    return {
        "reddit_sentiment": get_reddit_sentiment(),
        "news_sentiment": get_news_sentiment(),
        "fear_greed": get_fear_greed(),
        "google_trends": get_google_trends()
    }

if __name__ == "__main__":
    onchain = analyze_onchain()
    sentiment = analyze_sentiment()
    print("\nON-CHAIN\n")
    print(pd.DataFrame([onchain]).T)
    print("\nSENTIMENT\n")
    print(pd.DataFrame([sentiment]).T)
