import type { Trade } from "../api/types";

export function TradeLog({ trades }: { trades: Trade[] }) {
  if (!trades.length) return <p className="muted">本次回测没有平仓交易。</p>;
  return (
    <div className="table-wrap">
      <table className="trade-table">
        <thead>
          <tr>
            <th>入场</th>
            <th>出场</th>
            <th>数量</th>
            <th>买价</th>
            <th>卖价</th>
            <th>盈亏</th>
            <th>收益率</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, i) => (
            <tr key={i}>
              <td>{t.entry_ts.slice(0, 10)}</td>
              <td>{t.exit_ts.slice(0, 10)}</td>
              <td>{t.qty.toFixed(2)}</td>
              <td>{t.entry_price.toFixed(2)}</td>
              <td>{t.exit_price.toFixed(2)}</td>
              <td className={t.pnl >= 0 ? "pos" : "neg"}>{t.pnl >= 0 ? "+" : ""}{t.pnl.toFixed(2)}</td>
              <td className={t.return_pct >= 0 ? "pos" : "neg"}>
                {(t.return_pct * 100).toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
