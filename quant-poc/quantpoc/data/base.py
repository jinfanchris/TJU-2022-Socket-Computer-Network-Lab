"""DataSource abstraction.

Every adapter returns the *same* shape: a pandas DataFrame indexed by a
timezone-naive DatetimeIndex named ``ts`` with float columns
``open, high, low, close, volume``. That uniformity is what lets the rest of
the engine (indicators, backtest, replay) stay data-source-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterator

import pandas as pd

from ..models import Bar

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataSource(ABC):
    """Abstract market-data provider."""

    #: short identifier, e.g. "synthetic", "yfinance"
    name: str = "base"

    @abstractmethod
    def history(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Return OHLCV history. Index=ts, columns=OHLCV_COLUMNS."""

    @abstractmethod
    def symbols(self) -> list[dict]:
        """Return selectable symbols as ``[{"symbol": ..., "label": ...}]``."""

    def stream(
        self, symbol: str, timeframe: str = "1d", limit: int | None = None
    ) -> Iterator[Bar]:
        """Yield bars one at a time. Default: replay ``history`` bar by bar.

        Live adapters may override this to poll a real feed.
        """
        df = self.history(symbol, timeframe, limit=limit)
        for ts, row in df.iterrows():
            yield Bar(
                ts=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce an arbitrary OHLCV frame into the canonical shape."""
    df = df.rename(columns={c: c.lower() for c in df.columns})
    missing = [c for c in OHLCV_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"data is missing columns: {missing}")
    df = df[OHLCV_COLUMNS].astype(float)
    df.index = pd.to_datetime(df.index)
    df.index.name = "ts"
    return df.sort_index()
