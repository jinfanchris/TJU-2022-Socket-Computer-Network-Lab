import { useEffect, useRef } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, UTCTimestamp } from "lightweight-charts";
import type { Candle, Signal } from "../api/types";

const OVERLAY_COLORS = ["#f5a623", "#4a90e2", "#bd10e0", "#7ed321", "#50e3c2"];

function toTime(ts: string): UTCTimestamp {
  return Math.floor(new Date(ts).getTime() / 1000) as UTCTimestamp;
}

/**
 * TradingView lightweight-charts candlestick with MA/BBands overlays and
 * buy/sell markers. Overlay indicators are any indicator column passed in
 * `overlays` (already aligned to `candles`).
 */
export function CandleChart({
  candles,
  overlays,
  signals,
}: {
  candles: Candle[];
  overlays: Record<string, (number | null)[]>;
  signals?: Signal[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const lineSeriesRef = useRef<Record<string, ISeriesApi<"Line">>>({});

  // create chart once
  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#0f1420" },
        textColor: "#c7ccd6",
      },
      grid: { vertLines: { color: "#1c2431" }, horzLines: { color: "#1c2431" } },
      timeScale: { borderColor: "#2a3444" },
      rightPriceScale: { borderColor: "#2a3444" },
      height: 420,
    });
    chartRef.current = chart;
    candleSeriesRef.current = chart.addCandlestickSeries({
      upColor: "#26a69a",
      downColor: "#ef5350",
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
      borderVisible: false,
    });

    const ro = new ResizeObserver(() => {
      if (containerRef.current)
        chart.applyOptions({ width: containerRef.current.clientWidth });
    });
    ro.observe(containerRef.current);
    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      lineSeriesRef.current = {};
    };
  }, []);

  // update data
  useEffect(() => {
    const chart = chartRef.current;
    const cs = candleSeriesRef.current;
    if (!chart || !cs) return;

    cs.setData(
      candles.map((c) => ({
        time: toTime(c.ts),
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    );

    // reconcile overlay line series
    const wanted = new Set(Object.keys(overlays));
    for (const key of Object.keys(lineSeriesRef.current)) {
      if (!wanted.has(key)) {
        chart.removeSeries(lineSeriesRef.current[key]);
        delete lineSeriesRef.current[key];
      }
    }
    let ci = 0;
    for (const [name, values] of Object.entries(overlays)) {
      let series = lineSeriesRef.current[name];
      if (!series) {
        series = chart.addLineSeries({
          color: OVERLAY_COLORS[ci % OVERLAY_COLORS.length],
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        lineSeriesRef.current[name] = series;
      }
      series.setData(
        values
          .map((v, i) => (v == null ? null : { time: toTime(candles[i].ts), value: v }))
          .filter((x): x is { time: UTCTimestamp; value: number } => x !== null),
      );
      ci++;
    }

    if (signals && signals.length) {
      cs.setMarkers(
        signals.map((s) => ({
          time: toTime(s.ts),
          position: s.type === "buy" ? "belowBar" : "aboveBar",
          color: s.type === "buy" ? "#26a69a" : "#ef5350",
          shape: s.type === "buy" ? "arrowUp" : "arrowDown",
          text: s.type === "buy" ? "买" : "卖",
        })),
      );
    } else {
      cs.setMarkers([]);
    }
    chart.timeScale().fitContent();
  }, [candles, overlays, signals]);

  return <div ref={containerRef} className="chart" />;
}
