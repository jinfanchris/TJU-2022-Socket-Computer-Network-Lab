import { useCallback, useRef, useState } from "react";
import { replayWsUrl } from "../api/client";

export interface LiveBar {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface LiveAccount {
  ts: string;
  cash: number;
  equity: number;
  unrealized_pnl: number;
  realized_pnl: number;
  position_qty: number;
  position_avg: number;
}

export interface LiveSignal {
  ts: string;
  type: "buy" | "sell";
  price: number;
}

export interface LiveState {
  running: boolean;
  bars: LiveBar[];
  equity: { ts: string; equity: number }[];
  account: LiveAccount | null;
  signals: LiveSignal[];
  metrics: Record<string, number> | null;
  error: string | null;
}

const EMPTY: LiveState = {
  running: false,
  bars: [],
  equity: [],
  account: null,
  signals: [],
  metrics: null,
  error: null,
};

export function useLiveFeed() {
  const [state, setState] = useState<LiveState>(EMPTY);
  const wsRef = useRef<WebSocket | null>(null);

  const stop = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setState((s) => ({ ...s, running: false }));
  }, []);

  const start = useCallback(
    (cfg: {
      symbol: string;
      strategy: { key: string; params: Record<string, number> };
      cash: number;
      speed: number;
      limit: number;
    }) => {
      wsRef.current?.close();
      setState({ ...EMPTY, running: true });
      const ws = new WebSocket(replayWsUrl());
      wsRef.current = ws;

      ws.onopen = () => ws.send(JSON.stringify({ action: "start", ...cfg }));
      ws.onmessage = (ev) => {
        const frame = JSON.parse(ev.data);
        setState((s) => {
          switch (frame.type) {
            case "bar":
              return { ...s, bars: [...s.bars, frame.bar].slice(-500) };
            case "portfolio":
              return {
                ...s,
                account: frame.snapshot,
                equity: [...s.equity, { ts: frame.snapshot.ts, equity: frame.snapshot.equity }].slice(-500),
              };
            case "signal":
              return { ...s, signals: [...s.signals, frame.signal].slice(-200) };
            case "done":
              return { ...s, metrics: frame.metrics, running: false };
            case "error":
              return { ...s, error: frame.message, running: false };
            default:
              return s;
          }
        });
      };
      ws.onerror = () =>
        setState((s) => ({ ...s, error: "WebSocket 连接失败", running: false }));
      ws.onclose = () => setState((s) => ({ ...s, running: false }));
    },
    [],
  );

  return { state, start, stop };
}
