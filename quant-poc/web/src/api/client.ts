import axios from "axios";
import type {
  BacktestResult,
  FactorMeta,
  IndicatorMeta,
  MetricMeta,
  StrategyMeta,
  SymbolMeta,
} from "./types";

const http = axios.create({ baseURL: "/api", timeout: 30000 });

export const api = {
  health: () => http.get("/health").then((r) => r.data),
  symbols: () => http.get<SymbolMeta[]>("/symbols").then((r) => r.data),
  indicators: () => http.get<IndicatorMeta[]>("/meta/indicators").then((r) => r.data),
  factors: () =>
    http
      .get<{ factors: FactorMeta[]; metrics: MetricMeta[] }>("/meta/factors")
      .then((r) => r.data),
  strategies: () => http.get<StrategyMeta[]>("/meta/strategies").then((r) => r.data),
  backtest: (body: {
    symbol: string;
    strategy: { key: string; params: Record<string, number> };
    cash: number;
    limit: number;
  }) => http.post<BacktestResult>("/backtest", body).then((r) => r.data),
};

// WebSocket URL for the live replay (same-origin, proxied by Vite in dev).
export function replayWsUrl(): string {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws/replay`;
}
