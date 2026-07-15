"""Strategy registry + factory, exposing params (with ranges) to clients."""
from __future__ import annotations

from ..indicators.registry import Param
from .base import Strategy
from .ma_crossover import MACrossoverStrategy

# key -> (class, description, param specs for the UI)
_STRATEGIES: dict[str, dict] = {
    "ma_crossover": {
        "cls": MACrossoverStrategy,
        "description": "快、慢两条均线交叉产生买卖信号：金叉买入、死叉清仓。长线单一持仓，最直观的入门策略。",
        "params": {
            "fast": Param(10, 2, 100, "快线周期"),
            "slow": Param(30, 5, 250, "慢线周期"),
        },
    },
}


def get_strategy(key: str, params: dict | None = None) -> Strategy:
    entry = _STRATEGIES.get(key)
    if entry is None:
        raise ValueError(f"unknown strategy '{key}'")
    return entry["cls"](**(params or {}))


STRATEGY_REGISTRY = _STRATEGIES
