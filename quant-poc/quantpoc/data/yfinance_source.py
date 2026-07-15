"""Real stock/ETF history via yfinance.

Imported lazily so the package works even when yfinance isn't installed
(the synthetic default never touches this module).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from .base import DataSource, _normalize

# yfinance interval strings keyed by our timeframe vocabulary.
_TF_MAP = {"1d": "1d", "1h": "1h", "1w": "1wk", "1m": "1mo"}

_DEFAULT_SYMBOLS = [
    {"symbol": "AAPL", "label": "Apple"},
    {"symbol": "MSFT", "label": "Microsoft"},
    {"symbol": "NVDA", "label": "NVIDIA"},
    {"symbol": "SPY", "label": "S&P 500 ETF"},
    {"symbol": "TSLA", "label": "Tesla"},
]


class YFinanceDataSource(DataSource):
    name = "yfinance"

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
        import yfinance as yf  # lazy import

        interval = _TF_MAP.get(timeframe, "1d")
        period = None
        if start is None and end is None:
            # Pick a period wide enough to satisfy `limit` daily bars.
            n = int(limit or 400)
            period = "5y" if n > 400 else "2y"

        raw = yf.download(
            symbol,
            start=start,
            end=end,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )
        if raw.empty:
            raise ValueError(f"yfinance returned no data for '{symbol}'")

        # yfinance may return a MultiIndex on columns for single tickers.
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        df = _normalize(raw)
        if limit:
            df = df.tail(int(limit))
        return df
