"""Simulated live trading — replays historical bars on an asyncio clock.

Same strategy + portfolio machinery as the backtest, but yields an event per
bar so the WebSocket can stream a "live" account to the UIs at a configurable
speed. This is the paper-trading / 模拟实盘 mode.
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

import pandas as pd

from ..indicators.registry import INDICATOR_REGISTRY
from ..models import Position
from ..strategy.base import Strategy, StrategyContext
from .portfolio import Portfolio


class ReplayFeed:
    def __init__(
        self,
        data: pd.DataFrame,
        strategy: Strategy,
        portfolio: Portfolio,
        symbol: str,
        speed: float = 8.0,
        warmup: int = 40,
        indicators: list[dict] | None = None,
    ) -> None:
        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio
        self.symbol = symbol
        self.speed = max(speed, 0.5)  # bars per second
        self.warmup = warmup
        self.indicators = indicators or [{"key": "sma", "params": {"length": 10}},
                                         {"key": "sma", "params": {"length": 30}}]

    def _indicator_values(self, hist: pd.DataFrame) -> dict[str, float]:
        out: dict[str, float] = {}
        for req in self.indicators:
            spec = INDICATOR_REGISTRY.get(req["key"])
            if spec is None:
                continue
            res = spec.compute(hist, req.get("params"))
            for col in res.columns:
                val = res[col].iloc[-1]
                out[col] = None if pd.isna(val) else float(val)
        return out

    async def stream(self) -> AsyncIterator[dict]:
        df = self.data
        pending = []
        n = len(df)

        for i, (ts, row) in enumerate(df.iterrows()):
            price_open = float(row["open"])
            price_close = float(row["close"])

            # fill previous bar's orders at this open
            for order in pending:
                fill = self.portfolio.submit(ts, self.symbol, order.side, order.qty, price_open)
                yield {
                    "type": "signal",
                    "signal": {"ts": ts.isoformat(), "type": order.side, "price": fill.price},
                }
            pending = []

            hist = df.iloc[: i + 1]
            pos = self.portfolio.positions.get(self.symbol, Position(symbol=self.symbol))
            ctx = StrategyContext(
                symbol=self.symbol, history=hist, position=pos, cash=self.portfolio.cash
            )
            if i >= self.warmup:
                pending = self.strategy.on_bar(ctx)

            self.portfolio.mark_to_market(ts, {self.symbol: price_close})
            snap = self.portfolio.snapshot(ts, {self.symbol: price_close})

            yield {
                "type": "bar",
                "bar": {
                    "ts": ts.isoformat(),
                    "open": price_open,
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": price_close,
                    "volume": float(row["volume"]),
                },
                "indicators": self._indicator_values(hist),
            }
            yield {
                "type": "portfolio",
                "snapshot": {
                    "ts": ts.isoformat(),
                    "cash": snap.cash,
                    "equity": snap.equity,
                    "unrealized_pnl": snap.unrealized_pnl,
                    "realized_pnl": snap.realized_pnl,
                    "position_qty": pos.qty,
                    "position_avg": pos.avg_price,
                },
            }
            await asyncio.sleep(1.0 / self.speed)

        from ..factors.metrics import compute_metrics

        yield {
            "type": "done",
            "metrics": compute_metrics(self.portfolio.equity_curve, self.portfolio.trades),
        }
