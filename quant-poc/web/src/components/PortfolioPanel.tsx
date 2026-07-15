import type { LiveAccount } from "../hooks/useLiveFeed";

export function PortfolioPanel({
  account,
  startingCash,
}: {
  account: LiveAccount | null;
  startingCash: number;
}) {
  if (!account) return <p className="muted">尚未开始。点击「开始回放」在虚拟账户上模拟实盘。</p>;
  const pnl = account.equity - startingCash;
  const pnlPct = (pnl / startingCash) * 100;
  return (
    <div className="account-grid">
      <Stat label="总权益" value={`$${account.equity.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
      <Stat label="现金" value={`$${account.cash.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
      <Stat
        label="累计盈亏"
        value={`${pnl >= 0 ? "+" : ""}${pnl.toFixed(0)} (${pnlPct.toFixed(2)}%)`}
        positive={pnl >= 0}
      />
      <Stat
        label="持仓"
        value={account.position_qty > 0 ? `${account.position_qty.toFixed(2)} @ ${account.position_avg.toFixed(2)}` : "空仓"}
      />
      <Stat
        label="浮动盈亏"
        value={`${account.unrealized_pnl >= 0 ? "+" : ""}${account.unrealized_pnl.toFixed(0)}`}
        positive={account.unrealized_pnl >= 0}
      />
    </div>
  );
}

function Stat({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${positive === undefined ? "" : positive ? "pos" : "neg"}`}>{value}</div>
    </div>
  );
}
