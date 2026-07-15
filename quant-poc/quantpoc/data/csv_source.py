"""CSV-backed data source.

Reads ``<csv_dir>/<SYMBOL>.csv``. The CSV must have a date/timestamp column
(``date``, ``datetime``, or ``ts``) plus OHLCV columns (case-insensitive).
A bundled ``data/samples/AAPL.csv`` lets CSV mode work offline out of the box.
"""
from __future__ import annotations

import glob
import os

import pandas as pd

from .base import DataSource, _normalize

_TS_CANDIDATES = ["date", "datetime", "ts", "timestamp", "time"]


class CsvDataSource(DataSource):
    name = "csv"

    def __init__(self, csv_dir: str = "data/samples") -> None:
        self.csv_dir = csv_dir

    def _path(self, symbol: str) -> str:
        return os.path.join(self.csv_dir, f"{symbol.upper()}.csv")

    def symbols(self) -> list[dict]:
        out = []
        for path in sorted(glob.glob(os.path.join(self.csv_dir, "*.csv"))):
            sym = os.path.splitext(os.path.basename(path))[0]
            out.append({"symbol": sym, "label": f"{sym} (CSV)"})
        return out

    def history(
        self,
        symbol: str,
        timeframe: str = "1d",
        start=None,
        end=None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        path = self._path(symbol)
        if not os.path.exists(path):
            raise FileNotFoundError(f"no CSV for symbol '{symbol}' at {path}")
        raw = pd.read_csv(path)

        lower = {c.lower(): c for c in raw.columns}
        ts_col = next((lower[c] for c in _TS_CANDIDATES if c in lower), None)
        if ts_col is None:
            raise ValueError(f"{path}: need a date column (one of {_TS_CANDIDATES})")
        raw = raw.set_index(ts_col)

        df = _normalize(raw)
        if start is not None:
            df = df[df.index >= pd.to_datetime(start)]
        if end is not None:
            df = df[df.index <= pd.to_datetime(end)]
        if limit:
            df = df.tail(int(limit))
        return df
