"""Pure-pandas technical indicator implementations.

Hand-written (no TA-Lib / pandas-ta build step) so a beginner can ``pip
install`` and run without native compilation. Each function takes the OHLCV
DataFrame plus params and returns a DataFrame whose columns are the named
outputs (e.g. ``RSI_14``), aligned to the input index.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(df: pd.DataFrame, length: int = 20) -> pd.DataFrame:
    out = df["close"].rolling(int(length)).mean()
    return out.to_frame(f"SMA_{length}")


def ema(df: pd.DataFrame, length: int = 20) -> pd.DataFrame:
    out = df["close"].ewm(span=int(length), adjust=False).mean()
    return out.to_frame(f"EMA_{length}")


def rsi(df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
    length = int(length)
    delta = df["close"].diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    # Wilder's smoothing.
    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.to_frame(f"RSI_{length}")


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    fast, slow, signal = int(fast), int(slow), int(signal)
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame(
        {
            f"MACD_{fast}_{slow}": macd_line,
            f"MACDsig_{signal}": signal_line,
            f"MACDhist": hist,
        }
    )


def bbands(df: pd.DataFrame, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    length = int(length)
    mid = df["close"].rolling(length).mean()
    dev = df["close"].rolling(length).std()
    upper = mid + float(std) * dev
    lower = mid - float(std) * dev
    return pd.DataFrame(
        {f"BBL_{length}": lower, f"BBM_{length}": mid, f"BBU_{length}": upper}
    )


def atr(df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
    length = int(length)
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    out = tr.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    return out.to_frame(f"ATR_{length}")


def volume(df: pd.DataFrame, length: int = 20) -> pd.DataFrame:
    """Raw volume plus its moving average, for a volume subpanel."""
    vma = df["volume"].rolling(int(length)).mean()
    return pd.DataFrame({"VOL": df["volume"], f"VOLMA_{length}": vma})
