"""Cross-sectional / time-series *factor* computations.

A factor turns raw prices into a single evolving number that (hopefully)
predicts future returns. These are intentionally simple, standard textbook
factors so the descriptions can stay honest and beginner-friendly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def momentum(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    """Trailing return over ``lookback`` bars — "what went up keeps going up"."""
    lookback = int(lookback)
    return df["close"].pct_change(lookback).rename(f"MOM_{lookback}")


def mean_reversion(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    """Z-score of price vs its moving average — how far "stretched" from normal.

    Positive = above average (rich), negative = below (cheap). Mean-reversion
    bets that extremes snap back toward zero.
    """
    lookback = int(lookback)
    ma = df["close"].rolling(lookback).mean()
    sd = df["close"].rolling(lookback).std()
    z = (df["close"] - ma) / sd.replace(0.0, np.nan)
    return z.rename(f"ZSCORE_{lookback}")


def volatility(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    """Annualized rolling volatility of daily returns (risk gauge)."""
    lookback = int(lookback)
    ret = df["close"].pct_change()
    vol = ret.rolling(lookback).std() * np.sqrt(252)
    return vol.rename(f"VOL_{lookback}")
