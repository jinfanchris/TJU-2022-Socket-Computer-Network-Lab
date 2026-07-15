import type { MetricMeta } from "../api/types";
import { InfoTip } from "./InfoTip";

function formatMetric(value: number, unit: string): { text: string; positive: boolean } {
  if (unit === "%") return { text: `${(value * 100).toFixed(2)}%`, positive: value >= 0 };
  if (unit === "ratio") return { text: value.toFixed(2), positive: value >= 0 };
  return { text: value.toFixed(2), positive: value >= 0 };
}

export function MetricsPanel({
  metrics,
  meta,
}: {
  metrics: Record<string, number>;
  meta: MetricMeta[];
}) {
  const metaByKey = Object.fromEntries(meta.map((m) => [m.key, m]));
  return (
    <div className="metrics-grid">
      {Object.entries(metrics).map(([key, value]) => {
        const m = metaByKey[key];
        const { text, positive } = formatMetric(value, m?.unit ?? "");
        return (
          <div className="metric-card" key={key}>
            <div className="metric-head">
              <span>{m?.name ?? key}</span>
              {m && (
                <InfoTip title={m.name} description={m.description} interpretation={m.interpretation} />
              )}
            </div>
            <div className={`metric-value ${positive ? "pos" : "neg"}`}>{text}</div>
          </div>
        );
      })}
    </div>
  );
}
