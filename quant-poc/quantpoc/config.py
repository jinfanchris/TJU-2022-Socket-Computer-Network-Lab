"""Runtime configuration.

A single ``DATA_MODE`` decides where market data comes from. Everything else
has a sensible default so the POC runs with zero setup (``DATA_MODE=synthetic``,
no network, no API keys).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

DataMode = Literal["synthetic", "csv", "yfinance", "ccxt"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QUANT_", env_file=".env", extra="ignore")

    # Where bars come from. "synthetic" needs nothing installed/online.
    data_mode: DataMode = "synthetic"

    # Default instrument + timeframe used when a request omits them.
    default_symbol: str = "SYNTH"
    default_timeframe: str = "1d"
    default_limit: int = 400

    # Virtual account starting cash and a flat commission (as a fraction).
    starting_cash: float = 100_000.0
    commission: float = 0.0005

    # CSV mode: directory holding <SYMBOL>.csv files.
    csv_dir: str = "data/samples"

    # ccxt mode: which exchange to pull public OHLCV from.
    ccxt_exchange: str = "binance"

    # CORS origins for the web dev server.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
