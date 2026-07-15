"""Offline synthetic data via geometric brownian motion.

This is the zero-dependency, zero-network default so the whole POC demos
without installing yfinance/ccxt or hitting the internet. Prices follow
``S_{t+1} = S_t * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)``; high/low/
volume are synthesized around each close so candlesticks look realistic.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .base import DataSource, _normalize

# A few named "instruments" with different drift/vol so the UI has variety.
_PRESETS: dict[str, dict] = {
    "SYNTH": {"start": 100.0, "mu": 0.10, "sigma": 0.20, "label": "Synthetic Trend"},
    "SYNTH-VOL": {"start": 50.0, "mu": 0.05, "sigma": 0.55, "label": "Synthetic High-Vol"},
    "SYNTH-BULL": {"start": 20.0, "mu": 0.35, "sigma": 0.25, "label": "Synthetic Bull"},
}

_TIMEFRAME_DAYS = {"1d": 1, "1h": 1 / 24, "1w": 7}


class SyntheticDataSource(DataSource):
    name = "synthetic"

    def __init__(self, seed: int = 42) -> None:
        # Fixed seed => reproducible demo. Each symbol gets a distinct stream.
        self._seed = seed

    def symbols(self) -> list[dict]:
        return [{"symbol": s, "label": p["label"]} for s, p in _PRESETS.items()]

    def history(
        self,
        symbol: str,
        timeframe: str = "1d",
        start=None,
        end=None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        preset = _PRESETS.get(symbol.upper(), _PRESETS["SYNTH"])
        n = int(limit or 400)
        dt = _TIMEFRAME_DAYS.get(timeframe, 1) / 252.0  # trading-year fraction

        # Deterministic per-symbol seed.
        rng = np.random.default_rng(self._seed + abs(hash(symbol.upper())) % 10_000)

        z = rng.standard_normal(n)
        mu, sigma, s0 = preset["mu"], preset["sigma"], preset["start"]
        log_ret = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
        close = s0 * np.exp(np.cumsum(log_ret))

        # Build OHLC around the close path.
        prev_close = np.concatenate([[s0], close[:-1]])
        open_ = prev_close
        intrabar = np.abs(rng.standard_normal(n)) * sigma * np.sqrt(dt) * close
        high = np.maximum(open_, close) + intrabar * 0.5
        low = np.minimum(open_, close) - intrabar * 0.5
        volume = (rng.lognormal(mean=12.0, sigma=0.4, size=n)).round()

        # Timestamps ending "today", stepping by the timeframe.
        step_days = _TIMEFRAME_DAYS.get(timeframe, 1)
        end_dt = datetime(2024, 12, 31)
        index = [end_dt - timedelta(days=step_days * (n - 1 - i)) for i in range(n)]

        df = pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
            index=pd.DatetimeIndex(index),
        )
        return _normalize(df)
