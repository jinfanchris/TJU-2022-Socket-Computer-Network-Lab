"""Rich renderable helpers shared by the TUI panels."""
from __future__ import annotations

from rich.table import Table
from rich.text import Text

_SPARK = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float], width: int = 40) -> str:
    """Unicode sparkline from a numeric series."""
    vals = [v for v in values if v is not None]
    if not vals:
        return ""
    if len(vals) > width:
        # simple decimation to fit width
        step = len(vals) / width
        vals = [vals[int(i * step)] for i in range(width)]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    return "".join(_SPARK[min(7, int((v - lo) / span * 7))] for v in vals)


def fmt_pct(x: float) -> Text:
    color = "green" if x >= 0 else "red"
    return Text(f"{x*100:+.2f}%", style=color)


def fmt_money(x: float) -> str:
    return f"${x:,.2f}"


def metrics_table(metrics: dict, metric_meta: list[dict]) -> Table:
    meta = {m["key"]: m for m in metric_meta}
    t = Table(title="绩效指标 Performance", expand=True, show_lines=False)
    t.add_column("指标", style="bold cyan")
    t.add_column("数值", justify="right")
    t.add_column("怎么看", style="dim", overflow="fold")
    for key, val in metrics.items():
        m = meta.get(key, {})
        name = m.get("name", key)
        unit = m.get("unit", "")
        if unit == "%":
            value = fmt_pct(val)
        elif unit == "ratio":
            value = Text(f"{val:.2f}", style="green" if val >= 0 else "red")
        else:
            value = Text(f"{val:.2f}")
        t.add_row(name, value, m.get("interpretation", ""))
    return t


def price_table(candles: list[dict], indicators: dict, last: int = 15) -> Table:
    t = Table(title="行情 K线 (最近)", expand=True)
    t.add_column("日期", style="cyan")
    t.add_column("开", justify="right")
    t.add_column("高", justify="right")
    t.add_column("低", justify="right")
    t.add_column("收", justify="right")
    for col in indicators:
        t.add_column(col, justify="right", style="yellow")
    rows = candles[-last:]
    offset = len(candles) - len(rows)
    for i, c in enumerate(rows):
        idx = offset + i
        cells = [
            c["ts"][:10],
            f"{c['open']:.2f}",
            f"{c['high']:.2f}",
            f"{c['low']:.2f}",
            f"{c['close']:.2f}",
        ]
        for col, series in indicators.items():
            v = series[idx] if idx < len(series) else None
            cells.append(f"{v:.2f}" if v is not None else "—")
        t.add_row(*cells)
    return t
