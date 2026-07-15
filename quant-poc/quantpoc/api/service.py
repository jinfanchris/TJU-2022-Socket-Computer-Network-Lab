"""Orchestration: wire data + indicators + strategy + engine together.

Holds an in-memory store of backtest runs keyed by ``run_id`` (no DB — this is
a POC). Both REST and WebSocket handlers call into this module so there's a
single place that knows how to assemble a run.
"""
from __future__ import annotations

import hashlib

import pandas as pd

from ..config import get_settings
from ..data.factory import get_data_source
from ..engine.backtest import BacktestEngine, BacktestResult
from ..engine.portfolio import Portfolio
from ..factors.registry import compute_factors
from ..indicators.registry import compute_indicators
from ..strategy.registry import get_strategy

# run_id -> BacktestResult
_RUN_STORE: dict[str, BacktestResult] = {}

# default indicator overlays applied to every backtest so the chart is useful
_DEFAULT_BT_INDICATORS = [
    {"key": "sma", "params": {"length": 10}},
    {"key": "sma", "params": {"length": 30}},
]


def get_candles(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    return get_data_source().history(symbol, timeframe, limit=limit)


def candles_to_list(df: pd.DataFrame) -> list[dict]:
    return [
        {
            "ts": ts.isoformat(),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": float(r["volume"]),
        }
        for ts, r in df.iterrows()
    ]


def compute(symbol, timeframe, limit, indicators, factors) -> dict:
    df = get_candles(symbol, timeframe, limit)
    return {
        "columns": compute_indicators(df, indicators),
        "factors": compute_factors(df, factors),
    }


def _run_id(symbol, timeframe, strat_cfg, cash) -> str:
    raw = f"{symbol}:{timeframe}:{strat_cfg.key}:{strat_cfg.params}:{cash}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def run_backtest(body) -> dict:
    df = get_candles(body.symbol, body.timeframe, body.limit)

    strategy = get_strategy(body.strategy.key, body.strategy.params)
    strategy.symbol = body.symbol  # engine reads this off the strategy

    portfolio = Portfolio(cash=body.cash, commission=get_settings().commission)
    engine = BacktestEngine(df, strategy, portfolio)
    result = engine.run()

    run_id = _run_id(body.symbol, body.timeframe, body.strategy, body.cash)
    result.run_id = run_id
    result.timeframe = body.timeframe

    # attach indicator overlays for the chart
    ind_reqs = body.indicators or _DEFAULT_BT_INDICATORS
    result.indicators = compute_indicators(df, [
        r if isinstance(r, dict) else {"key": r.key, "params": r.params} for r in ind_reqs
    ])

    _RUN_STORE[run_id] = result
    return _result_to_dict(result)


def get_run(run_id: str) -> dict | None:
    result = _RUN_STORE.get(run_id)
    return _result_to_dict(result) if result else None


def get_portfolio_snapshot(run_id: str) -> dict | None:
    result = _RUN_STORE.get(run_id)
    if not result or not result.portfolio:
        return None
    last_close = float(result.candles["close"].iloc[-1])
    last_ts = result.candles.index[-1]
    snap = result.portfolio.snapshot(last_ts, {result.symbol: last_close})
    return {
        "ts": last_ts.isoformat(),
        "cash": snap.cash,
        "equity": snap.equity,
        "unrealized_pnl": snap.unrealized_pnl,
        "realized_pnl": snap.realized_pnl,
        "positions": [
            {"symbol": p.symbol, "qty": p.qty, "avg_price": p.avg_price}
            for p in snap.positions
        ],
    }


def _result_to_dict(result: BacktestResult) -> dict:
    return {
        "run_id": result.run_id,
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "candles": candles_to_list(result.candles),
        "indicators": result.indicators,
        "equity_curve": [
            {"ts": p.ts.isoformat(), "equity": p.equity, "cash": p.cash}
            for p in result.equity_curve
        ],
        "trades": [
            {
                "symbol": t.symbol,
                "entry_ts": t.entry_ts.isoformat(),
                "exit_ts": t.exit_ts.isoformat(),
                "qty": t.qty,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": t.pnl,
                "return_pct": t.return_pct,
            }
            for t in result.trades
        ],
        "signals": result.signals,
        "metrics": result.metrics,
    }
