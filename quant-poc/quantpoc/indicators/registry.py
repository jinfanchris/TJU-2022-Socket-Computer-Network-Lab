"""Indicator registry — the single source of truth for both clients.

Every indicator carries plain-language ``description`` (what it is) and
``interpretation`` (how to read it) so the web app and TUI can teach a quant
beginner without duplicating any text. The API exposes this whole registry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from . import technical as T


@dataclass
class Param:
    default: float
    min: float
    max: float
    label: str = ""


@dataclass
class IndicatorSpec:
    key: str
    name: str
    category: str  # trend | momentum | volatility | volume
    description: str  # plain language: what it is
    interpretation: str  # plain language: how to read it
    fn: Callable[..., pd.DataFrame]
    params: dict[str, Param] = field(default_factory=dict)
    overlay: bool = True  # True => draw on the price chart; False => own subpanel

    def defaults(self) -> dict:
        return {k: p.default for k, p in self.params.items()}

    def compute(self, df: pd.DataFrame, params: dict | None = None) -> pd.DataFrame:
        merged = {**self.defaults(), **(params or {})}
        return self.fn(df, **merged)


INDICATOR_REGISTRY: dict[str, IndicatorSpec] = {
    "sma": IndicatorSpec(
        key="sma",
        name="简单移动平均线 (SMA)",
        category="trend",
        description="最近 N 根 K 线收盘价的算术平均值，随价格滑动。是最基础的趋势线。",
        interpretation="价格在均线之上通常视为偏多、之下偏空；短期均线上穿长期均线常被看作买入信号（金叉），下穿为卖出信号（死叉）。",
        fn=T.sma,
        params={"length": Param(20, 2, 200, "周期")},
        overlay=True,
    ),
    "ema": IndicatorSpec(
        key="ema",
        name="指数移动平均线 (EMA)",
        category="trend",
        description="和 SMA 类似，但给最近的价格更高权重，因此对最新走势反应更快。",
        interpretation="比 SMA 更贴近价格、拐头更早，但也更容易受短期噪音影响。常用 12/26 周期。",
        fn=T.ema,
        params={"length": Param(20, 2, 200, "周期")},
        overlay=True,
    ),
    "rsi": IndicatorSpec(
        key="rsi",
        name="相对强弱指数 (RSI)",
        category="momentum",
        description="衡量最近上涨力度与下跌力度的比值，取值 0–100，反映买卖双方谁更强。",
        interpretation="通常 RSI>70 视为超买（可能回落），RSI<30 视为超卖（可能反弹）。趋势行情里可长期停留在高位或低位。",
        fn=T.rsi,
        params={"length": Param(14, 2, 100, "周期")},
        overlay=False,
    ),
    "macd": IndicatorSpec(
        key="macd",
        name="MACD 指数平滑异同",
        category="momentum",
        description="用快、慢两条 EMA 的差（MACD 线）与其信号线、柱状图，捕捉动能与趋势转折。",
        interpretation="MACD 线上穿信号线为看多信号、下穿为看空；柱状图由负转正代表动能转强。",
        fn=T.macd,
        params={
            "fast": Param(12, 2, 50, "快线"),
            "slow": Param(26, 5, 100, "慢线"),
            "signal": Param(9, 2, 50, "信号"),
        },
        overlay=False,
    ),
    "bbands": IndicatorSpec(
        key="bbands",
        name="布林带 (Bollinger Bands)",
        category="volatility",
        description="以移动平均为中轨，上下各加减 N 倍标准差形成通道，通道宽度反映波动大小。",
        interpretation="价格触及上轨偏强、触及下轨偏弱；通道收窄常预示大波动将至（突破）。",
        fn=T.bbands,
        params={"length": Param(20, 5, 100, "周期"), "std": Param(2.0, 1.0, 4.0, "倍数")},
        overlay=True,
    ),
    "atr": IndicatorSpec(
        key="atr",
        name="平均真实波幅 (ATR)",
        category="volatility",
        description="衡量每根 K 线的平均波动幅度，数值越大代表行情越剧烈。常用于设置止损。",
        interpretation="ATR 本身不判方向，只看波动大小；很多人用「入场价 ± 2×ATR」来放置止损。",
        fn=T.atr,
        params={"length": Param(14, 2, 100, "周期")},
        overlay=False,
    ),
    "volume": IndicatorSpec(
        key="volume",
        name="成交量 (Volume)",
        category="volume",
        description="每根 K 线的成交数量，配合均量线观察资金参与度。",
        interpretation="放量上涨说明买盘积极、更可信；缩量或量价背离往往意味着趋势乏力。",
        fn=T.volume,
        params={"length": Param(20, 2, 100, "均量周期")},
        overlay=False,
    ),
}


def compute_indicators(
    df: pd.DataFrame, requests: list[dict]
) -> dict[str, list]:
    """Compute a list of indicators and return ``{column_name: [values]}``.

    Each request is ``{"key": "rsi", "params": {"length": 14}}``. NaNs become
    ``None`` so the JSON is valid and the chart can skip warm-up gaps.
    """
    out: dict[str, list] = {}
    for req in requests:
        spec = INDICATOR_REGISTRY.get(req["key"])
        if spec is None:
            continue
        result = spec.compute(df, req.get("params"))
        for col in result.columns:
            series = result[col]
            out[col] = [None if pd.isna(v) else float(v) for v in series]
    return out
