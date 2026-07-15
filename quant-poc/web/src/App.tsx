import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { api } from "./api/client";
import type {
  BacktestResult,
  FactorMeta,
  IndicatorMeta,
  MetricMeta,
  StrategyMeta,
  SymbolMeta,
} from "./api/types";
import { CandleChart } from "./components/CandleChart";
import { EquityCurve } from "./components/EquityCurve";
import { MetricsPanel } from "./components/MetricsPanel";
import { IndicatorPanel } from "./components/IndicatorPanel";
import { FactorPanel } from "./components/FactorPanel";
import { TradeLog } from "./components/TradeLog";
import { PortfolioPanel } from "./components/PortfolioPanel";
import { InfoTip } from "./components/InfoTip";
import { useLiveFeed } from "./hooks/useLiveFeed";

type Tab = "backtest" | "live" | "learn";

export default function App() {
  const [dataMode, setDataMode] = useState("");
  const [symbols, setSymbols] = useState<SymbolMeta[]>([]);
  const [strategies, setStrategies] = useState<StrategyMeta[]>([]);
  const [indicators, setIndicators] = useState<IndicatorMeta[]>([]);
  const [factors, setFactors] = useState<FactorMeta[]>([]);
  const [metricsMeta, setMetricsMeta] = useState<MetricMeta[]>([]);

  const [symbol, setSymbol] = useState("");
  const [strategyKey, setStrategyKey] = useState("ma_crossover");
  const [fast, setFast] = useState(10);
  const [slow, setSlow] = useState(30);
  const [cash, setCash] = useState(100000);
  const [speed, setSpeed] = useState(12);

  const [tab, setTab] = useState<Tab>("backtest");
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [factorValues, setFactorValues] = useState<Record<string, (number | null)[]>>({});
  const [activeOverlays, setActiveOverlays] = useState<Set<string>>(new Set(["sma"]));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const live = useLiveFeed();

  // bootstrap metadata
  useEffect(() => {
    (async () => {
      try {
        const [h, syms, strat, inds, fac] = await Promise.all([
          api.health(),
          api.symbols(),
          api.strategies(),
          api.indicators(),
          api.factors(),
        ]);
        setDataMode(h.data_mode);
        setSymbols(syms);
        setSymbol(syms[0]?.symbol ?? "");
        setStrategies(strat);
        setStrategyKey(strat[0]?.key ?? "ma_crossover");
        setIndicators(inds);
        setFactors(fac.factors);
        setMetricsMeta(fac.metrics);
      } catch (e) {
        setError("无法连接后端，请先运行 uvicorn quantpoc.api.app:app --port 8000");
      }
    })();
  }, []);

  const runBacktest = async () => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.backtest({
        symbol,
        strategy: { key: strategyKey, params: { fast, slow } },
        cash,
        limit: 400,
      });
      setResult(res);
      // compute factor series for the factor panel
      const fv = await axios.post("/api/indicators", {
        symbol,
        limit: 400,
        indicators: [],
        factors: factors.map((f) => ({ key: f.key, params: {} })),
      });
      setFactorValues(fv.data.factors ?? {});
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  // run once symbol is known
  useEffect(() => {
    if (symbol) runBacktest();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]);

  const overlays = useMemo(() => {
    if (!result) return {};
    const out: Record<string, (number | null)[]> = {};
    for (const [name, series] of Object.entries(result.indicators)) {
      const key = name.toLowerCase();
      const on =
        (activeOverlays.has("sma") && key.startsWith("sma")) ||
        (activeOverlays.has("ema") && key.startsWith("ema")) ||
        (activeOverlays.has("bbands") && (key.startsWith("bbl") || key.startsWith("bbm") || key.startsWith("bbu")));
      if (on) out[name] = series;
    }
    return out;
  }, [result, activeOverlays]);

  const toggleOverlay = (key: string) =>
    setActiveOverlays((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });

  const startLive = () =>
    live.start({ symbol, strategy: { key: strategyKey, params: { fast, slow } }, cash, speed, limit: 200 });

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          量化交易 POC <span className="mode-badge">数据源: {dataMode || "…"}</span>
        </div>
        <div className="controls">
          <label>
            标的
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {symbols.map((s) => (
                <option key={s.symbol} value={s.symbol}>{s.label}</option>
              ))}
            </select>
          </label>
          <label>
            策略
            <select value={strategyKey} onChange={(e) => setStrategyKey(e.target.value)}>
              {strategies.map((s) => (
                <option key={s.key} value={s.key}>{s.name}</option>
              ))}
            </select>
          </label>
          <label>
            快线
            <input type="number" value={fast} onChange={(e) => setFast(+e.target.value)} />
          </label>
          <label>
            慢线
            <input type="number" value={slow} onChange={(e) => setSlow(+e.target.value)} />
          </label>
          <label>
            资金
            <input type="number" value={cash} onChange={(e) => setCash(+e.target.value)} />
          </label>
          <button className="primary" onClick={runBacktest} disabled={loading}>
            {loading ? "运行中…" : "运行回测"}
          </button>
        </div>
      </header>

      <nav className="tabs">
        <button className={tab === "backtest" ? "active" : ""} onClick={() => setTab("backtest")}>回测 Backtest</button>
        <button className={tab === "live" ? "active" : ""} onClick={() => setTab("live")}>模拟实盘 Live</button>
        <button className={tab === "learn" ? "active" : ""} onClick={() => setTab("learn")}>指标说明 Learn</button>
      </nav>

      {error && <div className="error-bar">{error}</div>}

      {tab === "backtest" && (
        <main className="grid-2">
          <section className="card chart-card">
            <h2>{symbol} · K线与指标</h2>
            {result ? (
              <CandleChart candles={result.candles} overlays={overlays} signals={result.signals} />
            ) : (
              <p className="muted">加载中…</p>
            )}
          </section>
          <aside>
            <IndicatorPanel indicators={indicators} active={activeOverlays} onToggle={toggleOverlay} />
          </aside>

          <section className="card">
            <h2>绩效指标</h2>
            {result && <MetricsPanel metrics={result.metrics} meta={metricsMeta} />}
          </section>
          <section className="card">
            <h2>量化因子（最新值）</h2>
            <FactorPanel factors={factors} values={factorValues} />
          </section>

          <section className="card">
            <h2>净值曲线</h2>
            {result && <EquityCurve data={result.equity_curve.map((p) => ({ ts: p.ts, equity: p.equity }))} />}
          </section>
          <section className="card">
            <h2>成交明细</h2>
            {result && <TradeLog trades={result.trades} />}
          </section>
        </main>
      )}

      {tab === "live" && (
        <main className="grid-1">
          <section className="card">
            <div className="live-controls">
              <h2>模拟实盘（历史回放）</h2>
              <div>
                <label>
                  速度
                  <input type="number" value={speed} min={1} max={60} onChange={(e) => setSpeed(+e.target.value)} />
                  <span className="muted"> 根/秒</span>
                </label>
                {live.state.running ? (
                  <button onClick={live.stop}>停止</button>
                ) : (
                  <button className="primary" onClick={startLive}>开始回放</button>
                )}
              </div>
            </div>
            <PortfolioPanel account={live.state.account} startingCash={cash} />
          </section>
          <section className="card">
            <h2>实时净值</h2>
            <EquityCurve data={live.state.equity} />
          </section>
          <section className="card">
            <h2>交易信号</h2>
            {live.state.signals.length === 0 ? (
              <p className="muted">等待信号…</p>
            ) : (
              <ul className="signal-list">
                {live.state.signals.slice(-20).reverse().map((s, i) => (
                  <li key={i} className={s.type}>
                    <span>{s.ts.slice(0, 10)}</span>
                    <span>{s.type === "buy" ? "买入" : "卖出"}</span>
                    <span>@ {s.price.toFixed(2)}</span>
                  </li>
                ))}
              </ul>
            )}
            {live.state.metrics && (
              <>
                <h3>回放结束 · 绩效</h3>
                <MetricsPanel metrics={live.state.metrics} meta={metricsMeta} />
              </>
            )}
          </section>
        </main>
      )}

      {tab === "learn" && (
        <main className="grid-1">
          <LearnSection title="技术指标 Indicators" items={indicators} />
          <LearnSection title="量化因子 Factors" items={factors} />
          <LearnSection
            title="绩效指标 Metrics"
            items={metricsMeta.map((m) => ({ ...m, category: "metric", params: {} }))}
          />
        </main>
      )}

      <footer className="foot">
        POC · 虚拟账户 · 默认合成数据可离线运行；切换 DATA_MODE 使用真实股票/加密行情
      </footer>
    </div>
  );
}

function LearnSection({
  title,
  items,
}: {
  title: string;
  items: { key: string; name: string; category: string; description: string; interpretation: string }[];
}) {
  return (
    <section className="card">
      <h2>{title}</h2>
      <div className="learn-grid">
        {items.map((it) => (
          <div className="learn-card" key={it.key}>
            <div className="learn-head">
              <strong>{it.name}</strong>
              <span className="tag">{it.category}</span>
            </div>
            <div className="learn-label">是什么</div>
            <p>{it.description}</p>
            <div className="learn-label">怎么看</div>
            <p>{it.interpretation}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
