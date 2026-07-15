"""End-to-end smoke tests for the quantpoc engine + API.

These mirror the manual verification checklist in the plan:
  * every indicator/factor/metric ships a plain-language explanation
  * a synthetic backtest produces the four headline metrics + trades
  * REST endpoints return the expected shapes
  * the /ws/replay WebSocket streams bar/portfolio/done frames

Run with:  make test   (or: pytest -q from quant-poc/)
Uses the default synthetic data mode, so no network or API keys are needed.
"""
from __future__ import annotations

from collections import Counter

import pytest
from fastapi.testclient import TestClient

from quantpoc.api.app import app
from quantpoc.factors.metrics import METRIC_REGISTRY
from quantpoc.factors.registry import FACTOR_REGISTRY
from quantpoc.indicators.registry import INDICATOR_REGISTRY


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ------------------------------------------------------ "explain everything"
def test_every_indicator_has_plain_language_docs():
    assert INDICATOR_REGISTRY, "no indicators registered"
    for spec in INDICATOR_REGISTRY.values():
        assert spec.description.strip(), f"{spec.key} missing description"
        assert spec.interpretation.strip(), f"{spec.key} missing interpretation"


def test_every_factor_and_metric_has_docs():
    for spec in FACTOR_REGISTRY.values():
        assert spec.description.strip() and spec.interpretation.strip(), spec.key
    for spec in METRIC_REGISTRY.values():
        assert spec.description.strip() and spec.interpretation.strip(), spec.key


# ----------------------------------------------------------------- REST API
def test_health(client: TestClient):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["data_mode"] == "synthetic"


def test_meta_endpoints_expose_descriptions(client: TestClient):
    inds = client.get("/api/meta/indicators").json()
    assert len(inds) == len(INDICATOR_REGISTRY)
    assert all(i["description"] and i["interpretation"] for i in inds)

    meta = client.get("/api/meta/factors").json()
    assert meta["factors"] and meta["metrics"]
    assert all(f["description"] for f in meta["factors"])

    strategies = client.get("/api/meta/strategies").json()
    assert any(s["key"] == "ma_crossover" for s in strategies)


def test_symbols_and_candles(client: TestClient):
    symbols = client.get("/api/symbols").json()
    assert symbols, "no symbols for synthetic mode"
    sym = symbols[0]["symbol"]
    candles = client.get("/api/candles", params={"symbol": sym, "limit": 120}).json()
    assert len(candles) == 120
    assert set(candles[0]) >= {"ts", "open", "high", "low", "close", "volume"}


def test_backtest_returns_metrics_and_trades(client: TestClient):
    resp = client.post(
        "/api/backtest",
        json={
            "symbol": "SYNTH",
            "strategy": {"key": "ma_crossover", "params": {"fast": 10, "slow": 30}},
            "cash": 100_000,
            "limit": 300,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    for key in ("cumulative_return", "sharpe", "max_drawdown", "win_rate"):
        assert key in data["metrics"]
    assert data["candles"] and data["equity_curve"]
    assert data["indicators"], "backtest should attach indicator overlays"
    assert isinstance(data["trades"], list)

    # stored run is retrievable + has a portfolio snapshot
    run_id = data["run_id"]
    assert client.get(f"/api/backtest/{run_id}").status_code == 200
    snap = client.get(f"/api/portfolio/{run_id}").json()
    assert snap["equity"] > 0


def test_compute_indicators_and_factors(client: TestClient):
    resp = client.post(
        "/api/indicators",
        json={
            "symbol": "SYNTH",
            "limit": 200,
            "indicators": [{"key": "rsi", "params": {"length": 14}}],
            "factors": [{"key": "momentum", "params": {}}],
        },
    )
    data = resp.json()
    assert any(c.startswith("RSI") for c in data["columns"])
    assert any(c.startswith("MOM") for c in data["factors"])


# ----------------------------------------------------------------- WebSocket
def test_replay_websocket_streams_frames(client: TestClient):
    with client.websocket_connect("/ws/replay") as ws:
        ws.send_json({"action": "start", "symbol": "SYNTH", "limit": 40, "speed": 200})
        types: list[str] = []
        while True:
            frame = ws.receive_json()
            types.append(frame["type"])
            if frame["type"] == "done":
                assert set(frame["metrics"]) >= {"sharpe", "max_drawdown"}
                break
    counts = Counter(types)
    assert counts["bar"] == 40
    assert counts["portfolio"] == 40
    assert counts["done"] == 1
