import type { FactorMeta } from "../api/types";
import { InfoTip } from "./InfoTip";

/**
 * Shows each quant factor's latest value (from the computed series) plus its
 * plain-language explanation.
 */
export function FactorPanel({
  factors,
  values,
}: {
  factors: FactorMeta[];
  values: Record<string, (number | null)[]>;
}) {
  const latest = (prefix: string): number | null => {
    const key = Object.keys(values).find((k) => k.startsWith(prefix));
    if (!key) return null;
    const series = values[key].filter((v) => v != null) as number[];
    return series.length ? series[series.length - 1] : null;
  };

  const prefixes: Record<string, string> = {
    momentum: "MOM",
    mean_reversion: "ZSCORE",
    volatility: "VOL",
  };

  return (
    <div className="factor-list">
      {factors.map((f) => {
        const v = latest(prefixes[f.key] ?? f.key.toUpperCase());
        return (
          <div className="factor-card" key={f.key}>
            <div className="factor-head">
              <span>{f.name}</span>
              <InfoTip title={f.name} description={f.description} interpretation={f.interpretation} />
            </div>
            <div className="factor-value">
              {v == null ? "—" : f.key === "volatility" ? `${(v * 100).toFixed(1)}%` : v.toFixed(3)}
            </div>
            <div className="factor-cat">{f.category}</div>
          </div>
        );
      })}
    </div>
  );
}
