"""Real crypto OHLCV via ccxt (public data, no API key needed).

Uses only public market-data endpoints, so no exchange credentials are
required for the POC. Imported lazily.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from .base import DataSource, _normalize

_TF_MAP = {"1d": "1d", "1h": "1h", "1w": "1w", "1m": "1M"}

_DEFAULT_SYMBOLS = [
    {"symbol": "BTC/USDT", "label": "Bitcoin"},
    {"symbol": "ETH/USDT", "label": "Ethereum"},
    {"symbol": "SOL/USDT", "label": "Solana"},
    {"symbol": "BNB/USDT", "label": "BNB"},
]


class CcxtDataSource(DataSource):
    name = "ccxt"

    def __init__(self, exchange: str = "binance") -> None:
        self._exchange_name = exchange
        self._exchange = None

    def _client(self):
        if self._exchange is None:
            import ccxt  # lazy import

            self._exchange = getattr(ccxt, self._exchange_name)({"enableRateLimit": True})
        return self._exchange

    def symbols(self) -> list[dict]:
        return _DEFAULT_SYMBOLS

    def history(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        client = self._client()
        tf = _TF_MAP.get(timeframe, "1d")
        since = int(start.timestamp() * 1000) if start else None
        rows = client.fetch_ohlcv(symbol, timeframe=tf, since=since, limit=int(limit or 400))
        if not rows:
            raise ValueError(f"ccxt returned no data for '{symbol}'")

        df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms")
        df = df.set_index("ts")
        return _normalize(df)
