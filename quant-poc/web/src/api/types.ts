// TS mirror of the Pydantic wire schemas.

export interface Param {
  default: number;
  min: number;
  max: number;
  label: string;
}

export interface IndicatorMeta {
  key: string;
  name: string;
  category: string;
  description: string;
  interpretation: string;
  params: Record<string, Param>;
  overlay: boolean;
}

export interface FactorMeta {
  key: string;
  name: string;
  category: string;
  description: string;
  interpretation: string;
  params: Record<string, Param>;
}

export interface MetricMeta {
  key: string;
  name: string;
  description: string;
  interpretation: string;
  unit: string;
}

export interface StrategyMeta {
  key: string;
  name: string;
  description: string;
  params: Record<string, Param>;
}

export interface SymbolMeta {
  symbol: string;
  label: string;
}

export interface Candle {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface EquityPoint {
  ts: string;
  equity: number;
  cash: number;
}

export interface Trade {
  symbol: string;
  entry_ts: string;
  exit_ts: string;
  qty: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
  return_pct: number;
}

export interface Signal {
  ts: string;
  type: "buy" | "sell";
  price: number;
}

export interface BacktestResult {
  run_id: string;
  symbol: string;
  timeframe: string;
  candles: Candle[];
  indicators: Record<string, (number | null)[]>;
  equity_curve: EquityPoint[];
  trades: Trade[];
  signals: Signal[];
  metrics: Record<string, number>;
}
