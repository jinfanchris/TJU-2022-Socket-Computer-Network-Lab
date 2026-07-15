"""WebSocket endpoint: streams a simulated-live (replay) trading session.

Client sends one JSON message to start:
    {"action":"start","symbol":"SYNTH","timeframe":"1d",
     "strategy":{"key":"ma_crossover","params":{"fast":10,"slow":30}},
     "cash":100000,"speed":8,"limit":300}
Server then streams bar / signal / portfolio / done frames until the history
is exhausted or the socket closes.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..config import get_settings
from ..engine.portfolio import Portfolio
from ..engine.replay import ReplayFeed
from ..strategy.registry import get_strategy
from . import service

router = APIRouter()


@router.websocket("/ws/replay")
async def ws_replay(ws: WebSocket):
    await ws.accept()
    try:
        cfg = await ws.receive_json()
        if cfg.get("action") != "start":
            await ws.send_json({"type": "error", "message": "expected action=start"})
            await ws.close()
            return

        symbol = cfg.get("symbol", get_settings().default_symbol)
        timeframe = cfg.get("timeframe", "1d")
        limit = int(cfg.get("limit", 300))
        cash = float(cfg.get("cash", get_settings().starting_cash))
        speed = float(cfg.get("speed", 8.0))
        strat_cfg = cfg.get("strategy", {"key": "ma_crossover", "params": {}})

        df = service.get_candles(symbol, timeframe, limit)
        strategy = get_strategy(strat_cfg.get("key", "ma_crossover"), strat_cfg.get("params", {}))
        strategy.symbol = symbol
        portfolio = Portfolio(cash=cash, commission=get_settings().commission)

        feed = ReplayFeed(df, strategy, portfolio, symbol=symbol, speed=speed)
        await ws.send_json({"type": "init", "symbol": symbol, "timeframe": timeframe})

        async for frame in feed.stream():
            await ws.send_json(frame)

    except WebSocketDisconnect:
        return
    except Exception as exc:  # surface engine errors to the client, then close
        try:
            await ws.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
