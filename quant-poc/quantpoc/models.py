"""Core domain types shared across the engine.

Deliberately plain dataclasses — the API layer converts them to Pydantic
schemas for the wire. Keeping the engine free of Pydantic makes it easy to
unit-test and reason about.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

Side = Literal["buy", "sell"]


@dataclass
class Bar:
    """One OHLCV candle."""

    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Order:
    """A market order. The POC only supports market orders."""

    ts: datetime
    symbol: str
    side: Side
    qty: float


@dataclass
class Fill:
    """An executed order."""

    ts: datetime
    symbol: str
    side: Side
    qty: float
    price: float
    commission: float


@dataclass
class Position:
    """A net long position in one symbol (POC is long-only)."""

    symbol: str
    qty: float = 0.0
    avg_price: float = 0.0

    def market_value(self, price: float) -> float:
        return self.qty * price

    def unrealized_pnl(self, price: float) -> float:
        return (price - self.avg_price) * self.qty


@dataclass
class Trade:
    """A closed round-trip, used to compute win rate / per-trade P&L."""

    symbol: str
    entry_ts: datetime
    exit_ts: datetime
    qty: float
    entry_price: float
    exit_price: float
    pnl: float

    @property
    def return_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.exit_price - self.entry_price) / self.entry_price


@dataclass
class EquityPoint:
    ts: datetime
    equity: float
    cash: float


@dataclass
class PortfolioSnapshot:
    ts: datetime
    cash: float
    equity: float
    positions: list[Position] = field(default_factory=list)
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
