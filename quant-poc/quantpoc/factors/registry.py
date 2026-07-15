"""Factor registry — same metadata shape as indicators.

Reusing the ``{key,name,category,description,interpretation,params,fn}``
contract means the clients render factor explanations with the exact same
component they use for indicators.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from ..indicators.registry import Param
from . import signals as S


@dataclass
class FactorSpec:
    key: str
    name: str
    category: str  # momentum | reversion | risk
    description: str
    interpretation: str
    fn: Callable[..., pd.Series]
    params: dict[str, Param] = field(default_factory=dict)

    def defaults(self) -> dict:
        return {k: p.default for k, p in self.params.items()}

    def compute(self, df: pd.DataFrame, params: dict | None = None) -> pd.Series:
        merged = {**self.defaults(), **(params or {})}
        return self.fn(df, **merged)


FACTOR_REGISTRY: dict[str, FactorSpec] = {
    "momentum": FactorSpec(
        key="momentum",
        name="动量因子 (Momentum)",
        category="momentum",
        description="过去一段时间的累计涨跌幅。核心假设是「强者恒强」——近期上涨的标的短期内倾向继续上涨。",
        interpretation="数值为正且越大，代表近期涨势越强；动量策略偏向买入高动量、回避负动量的标的。",
        fn=S.momentum,
        params={"lookback": Param(20, 2, 252, "回看周期")},
    ),
    "mean_reversion": FactorSpec(
        key="mean_reversion",
        name="均值回归因子 (Z-Score)",
        category="reversion",
        description="价格偏离其移动平均多少个标准差。衡量价格被「拉伸」的程度。",
        interpretation="Z 值 > +2 代表明显偏贵、可能回落；< −2 代表明显偏便宜、可能反弹。均值回归策略与动量相反，赌极端值回归。",
        fn=S.mean_reversion,
        params={"lookback": Param(20, 5, 252, "回看周期")},
    ),
    "volatility": FactorSpec(
        key="volatility",
        name="波动率因子 (Volatility)",
        category="risk",
        description="收益率的年化标准差，衡量价格波动/风险有多大。",
        interpretation="数值越高代表波动越剧烈、风险越大。可用于仓位管理（高波动降仓）或低波动选股策略。",
        fn=S.volatility,
        params={"lookback": Param(20, 5, 252, "回看周期")},
    ),
}


def compute_factors(df: pd.DataFrame, requests: list[dict]) -> dict[str, list]:
    """Compute factors -> ``{name: [values]}`` (NaN -> None for JSON)."""
    out: dict[str, list] = {}
    for req in requests:
        spec = FACTOR_REGISTRY.get(req["key"])
        if spec is None:
            continue
        series = spec.compute(df, req.get("params"))
        out[series.name] = [None if pd.isna(v) else float(v) for v in series]
    return out
