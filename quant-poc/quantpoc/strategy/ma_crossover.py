"""Moving-average crossover — the canonical demo strategy.

Go all-in long when the fast MA crosses above the slow MA (golden cross);
flatten when it crosses below (death cross). Long-only, all-in sizing keeps
the P&L easy to read for a beginner.
"""
from __future__ import annotations

from ..models import Order
from .base import Strategy, StrategyContext


class MACrossoverStrategy(Strategy):
    key = "ma_crossover"
    name = "均线金叉/死叉 (MA Crossover)"

    @staticmethod
    def default_params() -> dict:
        return {"fast": 10, "slow": 30}

    def on_bar(self, ctx: StrategyContext) -> list[Order]:
        fast_n = int(self.params["fast"])
        slow_n = int(self.params["slow"])
        close = ctx.history["close"]
        if len(close) < slow_n + 1:
            return []  # not enough history yet

        fast = close.rolling(fast_n).mean()
        slow = close.rolling(slow_n).mean()

        # Compare the last two bars to detect an actual crossover event.
        prev_diff = fast.iloc[-2] - slow.iloc[-2]
        curr_diff = fast.iloc[-1] - slow.iloc[-1]

        golden = prev_diff <= 0 < curr_diff
        death = prev_diff >= 0 > curr_diff

        orders: list[Order] = []
        if golden and ctx.position.qty == 0:
            qty = (ctx.cash * 0.99) / ctx.price  # keep a hair of cash for commission
            if qty > 0:
                orders.append(Order(ts=ctx.ts, symbol=ctx.symbol, side="buy", qty=qty))
        elif death and ctx.position.qty > 0:
            orders.append(
                Order(ts=ctx.ts, symbol=ctx.symbol, side="sell", qty=ctx.position.qty)
            )
        return orders
