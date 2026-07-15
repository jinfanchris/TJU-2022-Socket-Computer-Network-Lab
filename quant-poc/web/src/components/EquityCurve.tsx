import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function EquityCurve({
  data,
}: {
  data: { ts: string; equity: number }[];
}) {
  const points = data.map((p) => ({ ts: p.ts.slice(0, 10), equity: Math.round(p.equity) }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={points} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="eq" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4a90e2" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#4a90e2" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#1c2431" />
        <XAxis dataKey="ts" tick={{ fill: "#8b93a7", fontSize: 11 }} minTickGap={40} />
        <YAxis
          tick={{ fill: "#8b93a7", fontSize: 11 }}
          domain={["auto", "auto"]}
          width={70}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          contentStyle={{ background: "#161c2a", border: "1px solid #2a3444", color: "#e6e9f0" }}
          formatter={(v: number) => [`$${v.toLocaleString()}`, "净值"]}
        />
        <Area type="monotone" dataKey="equity" stroke="#4a90e2" fill="url(#eq)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
