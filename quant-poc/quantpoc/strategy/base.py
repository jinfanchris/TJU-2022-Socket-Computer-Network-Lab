"""Strategy interface.

A strategy sees a growing window of history each bar and returns market
orders. The backtest engine and the live replay feed both drive strategies
through the exact same ``on_bar`` contract.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from ..models import Order, Position


@dataclass
class StrategyContext:
    """Everything a strategy is allowed to look at on the current bar."""

    symbol: str
    history: pd.DataFrame  # OHLCV up to and including the current bar
    position: Position  # current holding (qty may be 0)
    cash: float

    @property
    def price(self) -> float:
        return float(self.history["close"].iloc[-1])

    @property
    def ts(self):
        return self.history.index[-1]


class Strategy(ABC):
    key: str = "base"
    name: str = "Base"

    def __init__(self, **params) -> None:
        self.params = {**self.default_params(), **params}

    @staticmethod
    def default_params() -> dict:
        return {}

    @abstractmethod
    def on_bar(self, ctx: StrategyContext) -> list[Order]:
        """Return orders to submit given the current context (may be empty)."""
