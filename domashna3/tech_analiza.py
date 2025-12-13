import warnings
warnings.filterwarnings("ignore")

from dataclasses import dataclass
from typing import Literal, Dict, Tuple
import numpy as np
import pandas as pd
import yfinance as yf
import ta



Timeframe = Literal["1D", "1W", "1M"]



def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        flat_cols = []
        for c in df.columns:
            if isinstance(c, tuple) and len(c) == 2:
                flat_cols.append(c[1])
            else:
                flat_cols.append(str(c))
        df.columns = flat_cols

    unique_cols = set(df.columns)
    if len(unique_cols) == 1:
        df.columns = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

    if "Adj Close" in df.columns and "Close" not in df.columns:
        df.rename(columns={"Adj Close": "Close"}, inplace=True)

    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    if not cols:
        raise KeyError(f"No valid OHLCV columns found! Got: {list(df.columns)}")

    df = df[cols].copy()

    if not np.issubdtype(df.index.dtype, np.datetime64):
        df.index = pd.to_datetime(df.index)

    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}

    out = df.resample(rule).agg(agg)
    out.dropna(inplace=True)
    return out



def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    close = d["Close"].squeeze()
    high = d["High"].squeeze()
    low = d["Low"].squeeze()
    volume = d["Volume"].squeeze()

    d["RSI_14"] = ta.momentum.RSIIndicator(close=close, window=14).rsi()

    macd = ta.trend.MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    d["MACD"] = macd.macd()
    d["MACD_SIGNAL"] = macd.macd_signal()
    d["MACD_HIST"] = macd.macd_diff()

    stoch = ta.momentum.StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
    d["STOCH_%K"] = stoch.stoch()

    adx_window = 14 if len(d) >= 14 else max(3, len(d) // 2)
    try:
        d["ADX_14"] = ta.trend.ADXIndicator(high=high, low=low, close=close, window=adx_window).adx()
    except Exception as e:
        print(f"[WARN] ADX skipped: {e}")
        d["ADX_14"] = np.nan

    d["CCI_20"] = ta.trend.CCIIndicator(high=high, low=low, close=close, window=20, constant=0.015).cci()

    d["SMA_20"] = ta.trend.SMAIndicator(close=close, window=20).sma_indicator()
    d["EMA_20"] = ta.trend.EMAIndicator(close=close, window=20).ema_indicator()
    d["WMA_20"] = close.rolling(window=20).apply(lambda x: ((x * range(1, 21)).sum()) / sum(range(1, 21)))

    bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2.0)
    d["BB_UPPER"] = bb.bollinger_hband()
    d["BB_LOWER"] = bb.bollinger_lband()

    d["VOL_MA_20"] = volume.rolling(20).mean()

    return d



@dataclass
class SignalConfig:
    rsi_buy: int = 30
    rsi_sell: int = 70
    stoch_buy: int = 20
    stoch_sell: int = 80
    cci_buy: int = -100
    cci_sell: int = 100
    adx_trend: int = 20


def rule_score_row(row: pd.Series, cfg: SignalConfig) -> Tuple[int, Dict[str, int]]:
    score_breakdown: Dict[str, int] = {}

    def safe_float(x):
        if isinstance(x, pd.Series):
            return float(x.values[-1]) if not x.empty else np.nan
        try:
            return float(x)
        except:
            return np.nan

    rsi = safe_float(row.get("RSI_14"))
    macd = safe_float(row.get("MACD"))
    macd_signal = safe_float(row.get("MACD_SIGNAL"))
    stoch_k = safe_float(row.get("STOCH_%K"))
    cci = safe_float(row.get("CCI_20"))
    adx = safe_float(row.get("ADX_14"))
    ema = safe_float(row.get("EMA_20"))
    sma = safe_float(row.get("SMA_20"))
    wma = safe_float(row.get("WMA_20"))
    bb_lower = safe_float(row.get("BB_LOWER"))
    bb_upper = safe_float(row.get("BB_UPPER"))
    vol_ma = safe_float(row.get("VOL_MA_20"))
    close = safe_float(row.get("Close"))
    volume = safe_float(row.get("Volume"))

    if not np.isnan(rsi):
        if rsi < cfg.rsi_buy:
            score_breakdown["RSI"] = +1
        elif rsi > cfg.rsi_sell:
            score_breakdown["RSI"] = -1
        else:
            score_breakdown["RSI"] = 0

    if not np.isnan(macd) and not np.isnan(macd_signal):
        score_breakdown["MACD"] = +1 if macd > macd_signal else -1

    if not np.isnan(stoch_k):
        if stoch_k < cfg.stoch_buy:
            score_breakdown["STOCH"] = +1
        elif stoch_k > cfg.stoch_sell:
            score_breakdown["STOCH"] = -1
        else:
            score_breakdown["STOCH"] = 0

    if not np.isnan(cci):
        if cci < cfg.cci_buy:
            score_breakdown["CCI"] = +1
        elif cci > cfg.cci_sell:
            score_breakdown["CCI"] = -1
        else:
            score_breakdown["CCI"] = 0

    adx_strong = not np.isnan(adx) and adx >= cfg.adx_trend

    ma_points = 0
    if not np.isnan(close) and not np.isnan(ema):
        ma_points += (+1 if close > ema else -1)
    if not np.isnan(close) and not np.isnan(sma):
        ma_points += (+1 if close > sma else -1)
    if not np.isnan(wma) and not np.isnan(ema):
        ma_points += (+1 if wma > ema else -1)
    if not np.isnan(bb_lower) and not np.isnan(bb_upper) and not np.isnan(close):
        if close < bb_lower:
            ma_points += +1
        elif close > bb_upper:
            ma_points += -1
    if not np.isnan(vol_ma) and vol_ma > 0 and not np.isnan(volume):
        if volume > vol_ma:
            ma_points += +1

    score_breakdown["MAs"] = (2 * ma_points) if adx_strong else ma_points

    total_score = int(sum(score_breakdown.values()))
    return total_score, score_breakdown


def generate_signals(df: pd.DataFrame, cfg: SignalConfig = SignalConfig()) -> pd.DataFrame:
    d = df.copy()
    scores = []
    details = []

    for _, row in d.iterrows():
        s, br = rule_score_row(row, cfg)
        scores.append(s)
        details.append(br)

    d["TA_SCORE"] = scores
    d["SIGNAL"] = np.where(
        d["TA_SCORE"] >= 2, "BUY", np.where(d["TA_SCORE"] <= -2, "SELL", "HOLD")
    )
    d["SCORE_BREAKDOWN"] = details
    return d



def load_price(symbol: str, start: str = "2024-01-01", end: str = None) -> pd.DataFrame:
    data = yf.download(symbol, start=start, end=end, interval="1d", auto_adjust=False, progress=False)
    data = data.dropna()
    return data

def analyze(symbol: str, timeframe: Timeframe = "1D", start: str = "2024-01-01", end: str = None) -> pd.DataFrame:
    raw = load_price(symbol, start, end)

    if timeframe == "1D":
        data = raw
    elif timeframe == "1W":
        data = resample_ohlcv(raw, "W")
    elif timeframe == "1M":
        data = resample_ohlcv(raw, "M")
    else:
        raise ValueError("timeframe must be one of: '1D','1W','1M'")

    data = add_indicators(data)
    data = generate_signals(data)
    return data



def latest_summary(df: pd.DataFrame) -> Dict[str, str]:
    last = df.iloc[-1]

    def safe_val(x):
        if isinstance(x, pd.Series):
            return float(x.values[-1]) if not x.empty else np.nan
        try:
            return float(x)
        except:
            return np.nan

    return {
        "date": str(df.index[-1].date()),
        "close": f"{safe_val(last['Close']):.2f}",
        "rsi14": f"{safe_val(last['RSI_14']):.2f}",
        "macd>signal": "YES" if safe_val(last["MACD"]) > safe_val(last["MACD_SIGNAL"]) else "NO",
        "stoch_k": f"{safe_val(last['STOCH_%K']):.2f}",
        "adx14": f"{safe_val(last['ADX_14']):.2f}",
        "cci20": f"{safe_val(last['CCI_20']):.2f}",
        "price_vs_ema20": "Above" if safe_val(last["Close"]) > safe_val(last["EMA_20"]) else "Below",
        "bb_zone": (
            "BelowLower"
            if safe_val(last["Close"]) < safe_val(last["BB_LOWER"])
            else (
                "AboveUpper"
                if safe_val(last["Close"]) > safe_val(last["BB_UPPER"])
                else "Inside"
            )
        ),
        "vol>volma20": "YES" if safe_val(last["Volume"]) > safe_val(last["VOL_MA_20"]) else "NO",
        "ta_score": f"{int(safe_val(last['TA_SCORE']))}",
        "signal": str(getattr(last["SIGNAL"], "values", [last["SIGNAL"]])[-1]),
    }



if __name__ == "__main__":
    for tf in ("1D", "1W", "1M"):
        df_tf = analyze("BTC-USD", timeframe=tf, start="2024-01-01")
        summary = latest_summary(df_tf)
        print(f"[{tf}] {summary}")

