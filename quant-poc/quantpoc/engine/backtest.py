"""Event-loop backtest engine.

For each bar we let the strategy decide using history *up to that bar*, then
fill any resulting orders at the *next* bar's open (avoiding look-ahead bias),
then mark the account to market. Small, explicit, and easy to explain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from ..factors.metrics import compute_metrics
from ..models import Order, Position
from ..strategy.base import Strategy, StrategyContext
from .portfolio import Portfolio


@dataclass
class BacktestResult:
    run_id: str
    symbol: str
    timeframe: str
    candles: pd.DataFrame  # OHLCV
    indicators: dict[str, list] = field(default_factory=dict)
    equity_curve: list = field(default_factory=list)  # list[EquityPoint]
    trades: list = field(default_factory=list)  # list[Trade]
    signals: list[dict] = field(default_factory=list)  # {ts,type,price}
    metrics: dict = field(default_factory=dict)
    portfolio: Portfolio | None = None


class BacktestEngine:
    def __init__(self, data: pd.DataFrame, strategy: Strategy, portfolio: Portfolio) -> None:
        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio

    def run(self, progress_cb: Callable[[float], None] | None = None) -> BacktestResult:
        df = self.data
        n = len(df)
        symbol = self.strategy.__dict__.get("symbol", "SYNTH")
        pending: list[Order] = []
        signals: list[dict] = []

        for i, (ts, row) in enumerate(df.iterrows()):
            price_open = float(row["open"])
            price_close = float(row["close"])

            # 1) Fill orders queued on the previous bar, at this bar's open.
            for order in pending:
                fill = self.portfolio.submit(
                    ts, symbol, order.side, order.qty, price_open
                )
                signals.append(
                    {"ts": ts.isoformat(), "type": order.side, "price": fill.price}
                )
            pending = []

            # 2) Ask the strategy for new orders using history through this bar.
            hist = df.iloc[: i + 1]
            pos = self.portfolio.positions.get(symbol, Position(symbol=symbol))
            ctx = StrategyContext(
                symbol=symbol, history=hist, position=pos, cash=self.portfolio.cash
            )
            pending = self.strategy.on_bar(ctx)

            # 3) Mark the account to market at the close.
            self.portfolio.mark_to_market(ts, {symbol: price_close})

            if progress_cb and (i % 25 == 0 or i == n - 1):
                progress_cb((i + 1) / n)

        metrics = compute_metrics(self.portfolio.equity_curve, self.portfolio.trades)
        return BacktestResult(
            run_id="",  # filled in by the service layer
            symbol=symbol,
            timeframe="",
            candles=df,
            equity_curve=self.portfolio.equity_curve,
            trades=self.portfolio.trades,
            signals=signals,
            metrics=metrics,
            portfolio=self.portfolio,
        )
