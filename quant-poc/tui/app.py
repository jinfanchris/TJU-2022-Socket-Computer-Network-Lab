"""Textual TUI client for the quantpoc engine.

Run (with the API server already up on :8000):
    python -m tui.app --api http://localhost:8000

Tabs:
  Backtest   — run the strategy over history, see K-line + indicators, equity
               sparkline, trade log, and performance metrics.
  Indicators — browse every indicator & factor with a plain-language 说明.
  Live       — stream a simulated-live (replay) session over WebSocket.
"""
from __future__ import annotations

import argparse

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from .api_client import ApiClient, replay_stream
from .widgets.render import (
    fmt_money,
    metrics_table,
    price_table,
    sparkline,
)


class QuantApp(App):
    CSS = """
    Screen { layout: vertical; }
    #controls { height: auto; padding: 1; background: $panel; }
    #controls Input, #controls Select { width: 18; }
    .col { padding: 1; }
    .card { border: round $primary; padding: 1; margin: 1 0; }
    #ind_list { height: 1fr; }
    #ind_detail { height: auto; }
    #live_log { height: 1fr; }
    Label.title { text-style: bold; color: $accent; }
    """
    BINDINGS = [
        ("r", "run_backtest", "运行回测"),
        ("l", "start_live", "模拟实盘"),
        ("q", "quit", "退出"),
    ]

    def __init__(self, api_url: str) -> None:
        super().__init__()
        self.api = ApiClient(api_url)
        self.symbols: list[dict] = []
        self.strategies: list[dict] = []
        self.indicators_meta: list[dict] = []
        self.factors_meta: dict = {"factors": [], "metrics": []}
        self._live_task = None

    # ------------------------------------------------------------------ layout
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="controls"):
            yield Label("标的")
            yield Select([("加载中…", "__loading__")], id="symbol", value="__loading__")
            yield Label("策略")
            yield Select([("加载中…", "__loading__")], id="strategy", value="__loading__")
            yield Label("快线")
            yield Input(value="10", id="fast", type="integer")
            yield Label("慢线")
            yield Input(value="30", id="slow", type="integer")
            yield Label("资金")
            yield Input(value="100000", id="cash", type="number")
            yield Button("运行回测 (r)", id="run", variant="success")
            yield Button("模拟实盘 (l)", id="live", variant="primary")

        with TabbedContent(initial="tab_bt"):
            with TabPane("回测 Backtest", id="tab_bt"):
                with VerticalScroll(classes="col"):
                    yield Static(self._welcome(), id="bt_metrics", classes="card")
                    yield Static("", id="bt_price", classes="card")
                    yield Static("", id="bt_trades", classes="card")
            with TabPane("指标/因子 Indicators", id="tab_ind"):
                with Horizontal():
                    with Vertical(classes="col"):
                        yield Label("指标与因子（选一项看说明）", classes="title")
                        yield DataTable(id="ind_list")
                    with VerticalScroll(classes="col"):
                        yield Static("", id="ind_detail", classes="card")
            with TabPane("模拟实盘 Live", id="tab_live"):
                with VerticalScroll(classes="col"):
                    yield Static("按 l 开始回放。账户随每根 K 线实时更新。", id="live_status", classes="card")
                    yield Static("", id="live_account", classes="card")
                    yield Static("", id="live_log", classes="card")
        yield Footer()

    def _welcome(self) -> Panel:
        txt = Text.from_markup(
            "[bold]量化交易 POC[/bold]\n\n"
            "选择标的与策略后按 [green]r[/green] 运行回测。\n"
            "回测会在虚拟账户上跑历史行情，显示 K 线、指标、净值与绩效。\n"
            "切到 [cyan]指标/因子[/cyan] 标签可查看每个指标的大白话解释。"
        )
        return Panel(txt, title="欢迎", border_style="green")

    # ------------------------------------------------------------------ startup
    async def on_mount(self) -> None:
        try:
            self.api.health()
        except Exception as exc:
            self.query_one("#bt_metrics", Static).update(
                Panel(f"无法连接 API：{exc}\n请先启动后端：uvicorn quantpoc.api.app:app --port 8000",
                      title="连接失败", border_style="red")
            )
            return

        self.symbols = self.api.symbols()
        self.strategies = self.api.strategies_meta()
        self.indicators_meta = self.api.indicators_meta()
        self.factors_meta = self.api.factors_meta()

        sym = self.query_one("#symbol", Select)
        sym.set_options([(s["label"], s["symbol"]) for s in self.symbols])
        if self.symbols:
            sym.value = self.symbols[0]["symbol"]

        strat = self.query_one("#strategy", Select)
        strat.set_options([(s["name"], s["key"]) for s in self.strategies])
        if self.strategies:
            strat.value = self.strategies[0]["key"]

        self._populate_indicator_table()
        self.action_run_backtest()

    def _populate_indicator_table(self) -> None:
        table = self.query_one("#ind_list", DataTable)
        table.clear(columns=True)
        table.add_columns("类型", "名称", "类别")
        self._meta_index: dict = {}
        for s in self.indicators_meta:
            key = f"ind::{s['key']}"
            table.add_row("指标", s["name"], s["category"], key=key)
            self._meta_index[key] = ("indicator", s)
        for s in self.factors_meta["factors"]:
            key = f"fac::{s['key']}"
            table.add_row("因子", s["name"], s["category"], key=key)
            self._meta_index[key] = ("factor", s)
        for m in self.factors_meta["metrics"]:
            key = f"met::{m['key']}"
            table.add_row("绩效", m["name"], "metric", key=key)
            self._meta_index[key] = ("metric", m)
        table.cursor_type = "row"

    # ------------------------------------------------------------------ actions
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            self.action_run_backtest()
        elif event.button.id == "live":
            self.action_start_live()

    def _current_params(self):
        symbol = self.query_one("#symbol", Select).value
        strategy = self.query_one("#strategy", Select).value
        try:
            fast = int(self.query_one("#fast", Input).value or 10)
            slow = int(self.query_one("#slow", Input).value or 30)
            cash = float(self.query_one("#cash", Input).value or 100000)
        except ValueError:
            fast, slow, cash = 10, 30, 100000.0
        return symbol, strategy, {"fast": fast, "slow": slow}, cash

    def action_run_backtest(self) -> None:
        symbol, strategy, params, cash = self._current_params()
        if not symbol:
            return
        try:
            res = self.api.backtest(symbol, strategy, params, cash, limit=300)
        except Exception as exc:
            self.query_one("#bt_metrics", Static).update(
                Panel(str(exc), title="回测失败", border_style="red")
            )
            return

        # metrics + equity sparkline
        eq = [p["equity"] for p in res["equity_curve"]]
        spark = sparkline(eq, 60)
        head = Text.from_markup(
            f"[bold]{symbol}[/bold]  策略={strategy}  初始资金={fmt_money(cash)}\n"
            f"净值曲线 {spark}\n"
        )
        mt = metrics_table(res["metrics"], self.factors_meta["metrics"])
        panel = Table.grid()
        panel.add_row(head)
        panel.add_row(mt)
        self.query_one("#bt_metrics", Static).update(
            Panel(panel, title="回测结果 Backtest", border_style="green")
        )

        self.query_one("#bt_price", Static).update(
            Panel(price_table(res["candles"], res["indicators"]),
                  title="K线 + 指标", border_style="cyan")
        )
        self.query_one("#bt_trades", Static).update(
            Panel(self._trades_table(res["trades"]), title="成交明细 Trades", border_style="magenta")
        )

    def _trades_table(self, trades: list[dict]) -> Table:
        t = Table(expand=True)
        t.add_column("入场", style="cyan")
        t.add_column("出场", style="cyan")
        t.add_column("数量", justify="right")
        t.add_column("买价", justify="right")
        t.add_column("卖价", justify="right")
        t.add_column("盈亏", justify="right")
        t.add_column("收益率", justify="right")
        if not trades:
            t.add_row("—", "—", "—", "—", "—", "无平仓交易", "—")
            return t
        for tr in trades[-12:]:
            pnl = tr["pnl"]
            style = "green" if pnl >= 0 else "red"
            t.add_row(
                tr["entry_ts"][:10], tr["exit_ts"][:10],
                f"{tr['qty']:.2f}", f"{tr['entry_price']:.2f}", f"{tr['exit_price']:.2f}",
                Text(f"{pnl:+.2f}", style=style),
                Text(f"{tr['return_pct']*100:+.2f}%", style=style),
            )
        return t

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None or not hasattr(self, "_meta_index"):
            return
        entry = self._meta_index.get(event.row_key.value)
        if not entry:
            return
        kind, meta = entry
        label = {"indicator": "指标", "factor": "因子", "metric": "绩效指标"}[kind]
        body = Text()
        body.append(f"{meta['name']}\n\n", style="bold yellow")
        body.append("是什么：\n", style="bold")
        body.append(meta["description"] + "\n\n")
        body.append("怎么看：\n", style="bold")
        body.append(meta["interpretation"] + "\n")
        params = meta.get("params")
        if params:
            body.append("\n参数：\n", style="bold")
            for k, p in params.items():
                body.append(f"  {p.get('label') or k}: 默认 {p['default']} (范围 {p['min']}–{p['max']})\n")
        self.query_one("#ind_detail", Static).update(
            Panel(body, title=f"{label} 说明", border_style="yellow")
        )

    # ------------------------------------------------------------------ live
    def action_start_live(self) -> None:
        if self._live_task and not self._live_task.done():
            return
        self.query_one(TabbedContent).active = "tab_live"
        symbol, strategy, params, cash = self._current_params()
        self._live_log_lines: list[str] = []
        self._live_task = self.run_worker(
            self._run_live(symbol, strategy, params, cash), exclusive=True
        )

    async def _run_live(self, symbol, strategy, params, cash) -> None:
        status = self.query_one("#live_status", Static)
        account = self.query_one("#live_account", Static)
        logw = self.query_one("#live_log", Static)
        status.update(Panel(f"回放中：{symbol} / {strategy}", border_style="green"))
        equity_hist: list[float] = []
        start_msg = {
            "action": "start", "symbol": symbol, "limit": 200, "speed": 12,
            "cash": cash, "strategy": {"key": strategy, "params": params},
        }
        try:
            async for frame in replay_stream(self.api.ws_url, start_msg):
                ftype = frame.get("type")
                if ftype == "portfolio":
                    s = frame["snapshot"]
                    equity_hist.append(s["equity"])
                    acc = Table.grid(padding=(0, 2))
                    acc.add_row("现金", fmt_money(s["cash"]))
                    acc.add_row("总权益", fmt_money(s["equity"]))
                    pnl = s["equity"] - cash
                    acc.add_row("累计盈亏", Text(f"{pnl:+,.2f}", style="green" if pnl >= 0 else "red"))
                    acc.add_row("持仓", f"{s['position_qty']:.2f} @ {s['position_avg']:.2f}")
                    acc.add_row("净值", sparkline(equity_hist, 50))
                    account.update(Panel(acc, title="虚拟账户 Account", border_style="cyan"))
                elif ftype == "signal":
                    sig = frame["signal"]
                    tag = "买入" if sig["type"] == "buy" else "卖出"
                    self._live_log_lines.append(f"{sig['ts'][:10]}  {tag} @ {sig['price']:.2f}")
                    logw.update(Panel("\n".join(self._live_log_lines[-15:]),
                                      title="交易信号 Signals", border_style="magenta"))
                elif ftype == "done":
                    status.update(Panel(
                        metrics_table(frame["metrics"], self.factors_meta["metrics"]),
                        title="回放结束 · 绩效", border_style="green"))
                elif ftype == "error":
                    status.update(Panel(frame["message"], title="错误", border_style="red"))
        except Exception as exc:
            status.update(Panel(str(exc), title="连接错误", border_style="red"))

    async def action_quit(self) -> None:
        self.api.close()
        self.exit()


def main() -> None:
    parser = argparse.ArgumentParser(description="quantpoc TUI")
    parser.add_argument("--api", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()
    QuantApp(args.api).run()


if __name__ == "__main__":
    main()
