"""REST endpoints. Thin wrappers over the service + registries."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..config import get_settings
from ..data.factory import get_data_source
from ..factors.metrics import METRIC_REGISTRY
from ..factors.registry import FACTOR_REGISTRY
from ..indicators.registry import INDICATOR_REGISTRY
from ..strategy.registry import STRATEGY_REGISTRY
from . import service
from .schemas import BacktestBody, ComputeIndicatorsBody

router = APIRouter(prefix="/api")


def _params_to_dict(params: dict) -> dict:
    return {
        k: {"default": p.default, "min": p.min, "max": p.max, "label": p.label}
        for k, p in params.items()
    }


@router.get("/health")
def health():
    return {"status": "ok", "data_mode": get_settings().data_mode}


@router.get("/meta/indicators")
def meta_indicators():
    return [
        {
            "key": s.key,
            "name": s.name,
            "category": s.category,
            "description": s.description,
            "interpretation": s.interpretation,
            "params": _params_to_dict(s.params),
            "overlay": s.overlay,
        }
        for s in INDICATOR_REGISTRY.values()
    ]


@router.get("/meta/factors")
def meta_factors():
    factors = [
        {
            "key": s.key,
            "name": s.name,
            "category": s.category,
            "description": s.description,
            "interpretation": s.interpretation,
            "params": _params_to_dict(s.params),
        }
        for s in FACTOR_REGISTRY.values()
    ]
    metrics = [
        {
            "key": m.key,
            "name": m.name,
            "description": m.description,
            "interpretation": m.interpretation,
            "unit": m.unit,
        }
        for m in METRIC_REGISTRY.values()
    ]
    return {"factors": factors, "metrics": metrics}


@router.get("/meta/strategies")
def meta_strategies():
    return [
        {
            "key": key,
            "name": entry["cls"].name,
            "description": entry["description"],
            "params": _params_to_dict(entry["params"]),
        }
        for key, entry in STRATEGY_REGISTRY.items()
    ]


@router.get("/symbols")
def symbols():
    return get_data_source().symbols()


@router.get("/candles")
def candles(
    symbol: str = Query(...),
    timeframe: str = "1d",
    limit: int = 400,
):
    try:
        df = service.get_candles(symbol, timeframe, limit)
    except Exception as exc:  # data-source errors -> 400 with a readable message
        raise HTTPException(status_code=400, detail=str(exc))
    return service.candles_to_list(df)


@router.post("/indicators")
def compute_indicators(body: ComputeIndicatorsBody):
    inds = [{"key": r.key, "params": r.params} for r in body.indicators]
    facs = [{"key": r.key, "params": r.params} for r in body.factors]
    try:
        return service.compute(body.symbol, body.timeframe, body.limit, inds, facs)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/backtest")
def backtest(body: BacktestBody):
    try:
        return service.run_backtest(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/backtest/{run_id}")
def get_backtest(run_id: str):
    result = service.get_run(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="run not found")
    return result


@router.get("/portfolio/{run_id}")
def get_portfolio(run_id: str):
    snap = service.get_portfolio_snapshot(run_id)
    if snap is None:
        raise HTTPException(status_code=404, detail="run not found")
    return snap
