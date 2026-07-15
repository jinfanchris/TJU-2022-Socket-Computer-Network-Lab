"""Virtual account: cash, positions, equity curve, and a closed-trade log.

Long-only for the POC. A "sell" that reduces a position books a closed
``Trade`` (used for win-rate). Commission is a flat fraction of notional.
"""
from __future__ import annotations

from ..models import (
    EquityPoint,
    Fill,
    Position,
    PortfolioSnapshot,
    Trade,
)


class Portfolio:
    def __init__(self, cash: float = 100_000.0, commission: float = 0.0005) -> None:
        self.starting_cash = cash
        self.cash = cash
        self.commission_rate = commission
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.fills: list[Fill] = []
        self.equity_curve: list[EquityPoint] = []
        self.realized_pnl = 0.0

    # ------------------------------------------------------------------ fills
    def submit(self, ts, symbol: str, side: str, qty: float, price: float) -> Fill:
        """Execute a market order at ``price`` and update the account."""
        commission = abs(qty * price) * self.commission_rate
        fill = Fill(ts=ts, symbol=symbol, side=side, qty=qty, price=price, commission=commission)
        self.apply_fill(fill)
        return fill

    def apply_fill(self, fill: Fill) -> None:
        self.fills.append(fill)
        pos = self.positions.get(fill.symbol, Position(symbol=fill.symbol))

        if fill.side == "buy":
            self.cash -= fill.qty * fill.price + fill.commission
            new_qty = pos.qty + fill.qty
            # weighted-average entry price
            pos.avg_price = (
                (pos.avg_price * pos.qty + fill.price * fill.qty) / new_qty
                if new_qty
                else 0.0
            )
            pos.qty = new_qty
            # remember when this open lot started (for the trade log)
            if not hasattr(pos, "_entry_ts") or pos.qty == fill.qty:
                pos._entry_ts = fill.ts  # type: ignore[attr-defined]
        else:  # sell (reduce/close a long)
            self.cash += fill.qty * fill.price - fill.commission
            pnl = (fill.price - pos.avg_price) * fill.qty - fill.commission
            self.realized_pnl += pnl
            self.trades.append(
                Trade(
                    symbol=fill.symbol,
                    entry_ts=getattr(pos, "_entry_ts", fill.ts),
                    exit_ts=fill.ts,
                    qty=fill.qty,
                    entry_price=pos.avg_price,
                    exit_price=fill.price,
                    pnl=pnl,
                )
            )
            pos.qty -= fill.qty
            if pos.qty <= 1e-9:
                pos.qty = 0.0
                pos.avg_price = 0.0

        self.positions[fill.symbol] = pos

    # ------------------------------------------------------------- valuation
    def equity(self, prices: dict[str, float]) -> float:
        holdings = sum(
            pos.market_value(prices.get(sym, pos.avg_price))
            for sym, pos in self.positions.items()
        )
        return self.cash + holdings

    def mark_to_market(self, ts, prices: dict[str, float]) -> None:
        self.equity_curve.append(
            EquityPoint(ts=ts, equity=self.equity(prices), cash=self.cash)
        )

    def snapshot(self, ts, prices: dict[str, float]) -> PortfolioSnapshot:
        unrealized = sum(
            pos.unrealized_pnl(prices.get(sym, pos.avg_price))
            for sym, pos in self.positions.items()
            if pos.qty
        )
        return PortfolioSnapshot(
            ts=ts,
            cash=self.cash,
            equity=self.equity(prices),
            positions=[p for p in self.positions.values() if p.qty],
            unrealized_pnl=unrealized,
            realized_pnl=self.realized_pnl,
        )
