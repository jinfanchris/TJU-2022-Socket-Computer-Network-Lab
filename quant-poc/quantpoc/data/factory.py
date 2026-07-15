"""The single place where data provenance is decided.

``get_data_source`` maps ``DATA_MODE`` to a concrete adapter. Clients never
know or care which one is active — swapping ``DATA_MODE`` needs no client edits.
"""
from __future__ import annotations

from functools import lru_cache

from ..config import get_settings
from .base import DataSource
from .csv_source import CsvDataSource
from .synthetic import SyntheticDataSource


@lru_cache
def get_data_source(mode: str | None = None) -> DataSource:
    settings = get_settings()
    mode = (mode or settings.data_mode).lower()

    if mode == "synthetic":
        return SyntheticDataSource()
    if mode == "csv":
        return CsvDataSource(csv_dir=settings.csv_dir)
    if mode == "yfinance":
        from .yfinance_source import YFinanceDataSource

        return YFinanceDataSource()
    if mode == "ccxt":
        from .ccxt_source import CcxtDataSource

        return CcxtDataSource(exchange=settings.ccxt_exchange)

    raise ValueError(f"unknown DATA_MODE '{mode}' (use synthetic|csv|yfinance|ccxt)")
