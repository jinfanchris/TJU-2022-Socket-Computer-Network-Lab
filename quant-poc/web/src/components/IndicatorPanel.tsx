import type { IndicatorMeta } from "../api/types";
import { InfoTip } from "./InfoTip";

/**
 * Lets the user toggle which overlay indicators are drawn on the candle chart,
 * each with its plain-language explanation. Only `overlay: true` indicators
 * (MA/EMA/BBands) can be drawn on the price chart in the POC.
 */
export function IndicatorPanel({
  indicators,
  active,
  onToggle,
}: {
  indicators: IndicatorMeta[];
  active: Set<string>;
  onToggle: (key: string) => void;
}) {
  const overlays = indicators.filter((i) => i.overlay);
  const others = indicators.filter((i) => !i.overlay);
  return (
    <div className="side-panel">
      <h3>叠加指标 Overlays</h3>
      {overlays.map((ind) => (
        <label className="toggle-row" key={ind.key}>
          <input
            type="checkbox"
            checked={active.has(ind.key)}
            onChange={() => onToggle(ind.key)}
          />
          <span>{ind.name}</span>
          <InfoTip title={ind.name} description={ind.description} interpretation={ind.interpretation} />
        </label>
      ))}
      <h3>其他指标 Reference</h3>
      {others.map((ind) => (
        <div className="toggle-row muted" key={ind.key}>
          <span>{ind.name}</span>
          <InfoTip title={ind.name} description={ind.description} interpretation={ind.interpretation} />
        </div>
      ))}
    </div>
  );
}
