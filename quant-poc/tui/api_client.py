"""Thin API client for the TUI — same endpoints the web app uses."""
from __future__ import annotations

import json

import httpx


class ApiClient:
    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(base_url=self.base_url, timeout=30.0)

    @property
    def ws_url(self) -> str:
        return self.base_url.replace("http", "ws", 1) + "/ws/replay"

    def health(self) -> dict:
        return self._http.get("/api/health").json()

    def indicators_meta(self) -> list[dict]:
        return self._http.get("/api/meta/indicators").json()

    def factors_meta(self) -> dict:
        return self._http.get("/api/meta/factors").json()

    def strategies_meta(self) -> list[dict]:
        return self._http.get("/api/meta/strategies").json()

    def symbols(self) -> list[dict]:
        return self._http.get("/api/symbols").json()

    def backtest(self, symbol: str, strategy_key: str, params: dict, cash: float, limit: int) -> dict:
        return self._http.post(
            "/api/backtest",
            json={
                "symbol": symbol,
                "strategy": {"key": strategy_key, "params": params},
                "cash": cash,
                "limit": limit,
            },
        ).json()

    def close(self) -> None:
        self._http.close()


async def replay_stream(ws_url: str, start_msg: dict):
    """Async generator yielding replay frames from the WebSocket."""
    import websockets

    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps(start_msg))
        async for raw in ws:
            yield json.loads(raw)
