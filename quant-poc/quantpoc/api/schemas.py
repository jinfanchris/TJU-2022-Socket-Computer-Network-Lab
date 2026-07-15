"""Pydantic wire schemas (what crosses the API boundary)."""
from __future__ import annotations

from pydantic import BaseModel


# ------------------------------------------------------------------ metadata
class ParamSchema(BaseModel):
    default: float
    min: float
    max: float
    label: str = ""


class IndicatorMeta(BaseModel):
    key: str
    name: str
    category: str
    description: str
    interpretation: str
    params: dict[str, ParamSchema]
    overlay: bool


class FactorMeta(BaseModel):
    key: str
    name: str
    category: str
    description: str
    interpretation: str
    params: dict[str, ParamSchema]


class MetricMeta(BaseModel):
    key: str
    name: str
    description: str
    interpretation: str
    unit: str


class StrategyMeta(BaseModel):
    key: str
    name: str
    description: str
    params: dict[str, ParamSchema]


class SymbolMeta(BaseModel):
    symbol: str
    label: str


# ------------------------------------------------------------------ market data
class Candle(BaseModel):
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class IndicatorRequest(BaseModel):
    key: str
    params: dict[str, float] = {}


class ComputeIndicatorsBody(BaseModel):
    symbol: str
    timeframe: str = "1d"
    limit: int = 400
    indicators: list[IndicatorRequest] = []
    factors: list[IndicatorRequest] = []


class ComputeIndicatorsResponse(BaseModel):
    columns: dict[str, list[float | None]]
    factors: dict[str, list[float | None]] = {}


# ------------------------------------------------------------------ backtest
class StrategyConfig(BaseModel):
    key: str = "ma_crossover"
    params: dict[str, float] = {}


class BacktestBody(BaseModel):
    symbol: str
    timeframe: str = "1d"
    limit: int = 400
    strategy: StrategyConfig = StrategyConfig()
    cash: float = 100_000.0
    indicators: list[IndicatorRequest] = []


class EquityPointSchema(BaseModel):
    ts: str
    equity: float
    cash: float


class TradeSchema(BaseModel):
    symbol: str
    entry_ts: str
    exit_ts: str
    qty: float
    entry_price: float
    exit_price: float
    pnl: float
    return_pct: float


class SignalSchema(BaseModel):
    ts: str
    type: str
    price: float


class BacktestResponse(BaseModel):
    run_id: str
    symbol: str
    timeframe: str
    candles: list[Candle]
    indicators: dict[str, list[float | None]]
    equity_curve: list[EquityPointSchema]
    trades: list[TradeSchema]
    signals: list[SignalSchema]
    metrics: dict[str, float]


class PositionSchema(BaseModel):
    symbol: str
    qty: float
    avg_price: float


class PortfolioSnapshotSchema(BaseModel):
    ts: str
    cash: float
    equity: float
    unrealized_pnl: float
    realized_pnl: float
    positions: list[PositionSchema]
