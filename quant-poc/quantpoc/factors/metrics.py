"""Performance metrics computed from an equity curve / trade list.

Each metric ships a plain-language description + interpretation via
``METRIC_REGISTRY`` so the "how good was this strategy?" cards can teach a
beginner what each number means.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..models import EquityPoint, Trade


@dataclass
class MetricSpec:
    key: str
    name: str
    description: str
    interpretation: str
    unit: str = ""  # "" | "%" | "ratio"


METRIC_REGISTRY: dict[str, MetricSpec] = {
    "cumulative_return": MetricSpec(
        key="cumulative_return",
        name="累计收益率",
        description="从开始到结束，账户净值总共增长了多少（相对初始资金）。",
        interpretation="越高越好。+0.30 表示资金增长了 30%。要结合承担的风险一起看。",
        unit="%",
    ),
    "sharpe": MetricSpec(
        key="sharpe",
        name="夏普比率 (Sharpe)",
        description="每承担一单位波动风险，换来多少超额收益。是「性价比」指标。",
        interpretation="通常 >1 算不错、>2 很好、<0 说明还不如不做。它惩罚剧烈波动的收益。",
        unit="ratio",
    ),
    "max_drawdown": MetricSpec(
        key="max_drawdown",
        name="最大回撤",
        description="账户净值从最高点跌到之后最低点的最大跌幅，衡量最坏的一段亏损。",
        interpretation="越接近 0 越好。−0.20 表示曾经从高点回落 20%，反映策略能让你多难受。",
        unit="%",
    ),
    "win_rate": MetricSpec(
        key="win_rate",
        name="胜率",
        description="所有已平仓交易中盈利交易所占的比例。",
        interpretation="55% 表示 100 笔里约 55 笔赚钱。胜率高不代表一定赚钱，还要看盈亏比。",
        unit="%",
    ),
}


def _equity_series(equity_curve: list[EquityPoint]) -> pd.Series:
    if not equity_curve:
        return pd.Series(dtype=float)
    return pd.Series([p.equity for p in equity_curve])


def compute_metrics(
    equity_curve: list[EquityPoint],
    trades: list[Trade],
    periods_per_year: int = 252,
) -> dict[str, float]:
    """Return the four headline metrics as plain floats."""
    eq = _equity_series(equity_curve)
    if len(eq) < 2:
        return {"cumulative_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0, "win_rate": 0.0}

    cumulative_return = float(eq.iloc[-1] / eq.iloc[0] - 1.0)

    rets = eq.pct_change().dropna()
    if rets.std() > 0:
        sharpe = float(rets.mean() / rets.std() * np.sqrt(periods_per_year))
    else:
        sharpe = 0.0

    running_max = eq.cummax()
    drawdown = eq / running_max - 1.0
    max_drawdown = float(drawdown.min())

    if trades:
        wins = sum(1 for t in trades if t.pnl > 0)
        win_rate = float(wins / len(trades))
    else:
        win_rate = 0.0

    return {
        "cumulative_return": cumulative_return,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
    }
