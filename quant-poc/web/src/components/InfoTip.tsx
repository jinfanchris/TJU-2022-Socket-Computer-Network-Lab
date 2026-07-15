import { useState } from "react";

/**
 * A small "?" badge that reveals a plain-language explanation on hover/click.
 * This is the single component that surfaces every indicator/factor/metric
 * description throughout the app — the "teach a beginner" requirement.
 */
export function InfoTip({
  title,
  description,
  interpretation,
}: {
  title: string;
  description: string;
  interpretation?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <span className="infotip" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <button className="infotip-badge" onClick={() => setOpen((o) => !o)} aria-label="说明">
        ?
      </button>
      {open && (
        <span className="infotip-pop">
          <strong>{title}</strong>
          <span className="infotip-label">是什么</span>
          <span>{description}</span>
          {interpretation && (
            <>
              <span className="infotip-label">怎么看</span>
              <span>{interpretation}</span>
            </>
          )}
        </span>
      )}
    </span>
  );
}
