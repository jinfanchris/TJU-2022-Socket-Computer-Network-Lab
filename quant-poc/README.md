# 量化交易 POC (Quant Trading POC)

一个用来入门量化交易的最小可运行原型：用**虚拟账户**在**历史回测**和**模拟实盘（历史回放）**两种模式下跑量化策略，直观查看 **K 线 / 技术指标 / 量化因子 / 账户盈亏 / 绩效指标**。

> 面向量化新手：**每一个指标、因子、绩效指标都配有大白话解释**（「是什么 + 怎么看」），在网页里悬停 `?` 或在 TUI 里选中即可查看。

一套 Python 引擎，两个瘦客户端：

```
                 ┌─────────────────────────┐
   React 网页 ──▶ │  FastAPI  (REST + WS)   │ ◀── Textual TUI
                 │   quantpoc 引擎          │
                 │  数据/指标/因子/回测/组合 │
                 └─────────────────────────┘
```

## 功能一览

- **数据源可切换**（一个环境变量 `QUANT_DATA_MODE`，客户端无感）：
  - `synthetic`（默认）— 几何布朗运动合成行情，**零联网、零 API key**，开箱即跑。
  - `csv` — 读取 `data/samples/<SYMBOL>.csv` 历史数据（内置 `AAPL.csv`）。
  - `yfinance` — 真实股票/ETF 历史行情。
  - `ccxt` — 真实加密货币行情（默认币安，公开数据无需密钥）。
- **技术指标**：SMA、EMA、RSI、MACD、布林带、ATR、成交量。
- **量化因子**：动量、均值回归（Z-Score）、波动率。
- **绩效指标**：累计收益、夏普比率、最大回撤、胜率。
- **虚拟账户**：现金、持仓、盈亏、净值曲线、成交明细。
- **回测**：均线金叉/死叉示例策略，次日开盘成交、含手续费。
- **模拟实盘**：按可调速度回放历史，账户随每根 K 线实时更新（WebSocket 推送）。

## 快速开始

### 1) 后端引擎（必需）

```bash
cd quant-poc
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn quantpoc.api.app:app --reload --port 8000
```

验证：`curl localhost:8000/api/health` → `{"status":"ok","data_mode":"synthetic"}`
交互式 API 文档：<http://localhost:8000/docs>

### 2) 网页界面

```bash
cd web
npm install
npm run dev          # http://localhost:5173（已自动代理 /api、/ws 到 :8000）
```

三个标签页：**回测 Backtest** / **模拟实盘 Live** / **指标说明 Learn**。

### 3) 终端界面 (TUI)

```bash
# 在后端已启动的前提下，另开一个终端：
cd quant-poc
python -m tui.app --api http://localhost:8000
```

快捷键：`r` 运行回测 · `l` 模拟实盘 · `q` 退出。

## 切换到真实数据

安装可选依赖并设置数据模式即可，**无需改任何客户端代码**：

```bash
pip install yfinance ccxt        # 真实数据依赖
export QUANT_DATA_MODE=yfinance   # 或 ccxt / csv
uvicorn quantpoc.api.app:app --reload --port 8000
```

- 股票（yfinance）：标的如 `AAPL`、`MSFT`、`SPY`。
- 加密（ccxt）：标的如 `BTC/USDT`、`ETH/USDT`。

其余配置见 `.env.example`（复制为 `.env`）。

## 目录结构

```
quant-poc/
├── quantpoc/            # Python 引擎（被两个客户端共用）
│   ├── data/           # 数据源适配器 + 工厂（synthetic/csv/yfinance/ccxt）
│   ├── indicators/     # 技术指标 + 带解释的注册表
│   ├── factors/        # 量化因子 + 绩效指标（含解释）
│   ├── strategy/       # 策略接口 + 均线金叉示例
│   ├── engine/         # 虚拟账户 / 回测引擎 / 回放
│   └── api/            # FastAPI：REST + WebSocket
├── tui/                # Textual 终端客户端
├── web/                # React + Vite + TypeScript 网页客户端
└── data/samples/       # 内置示例 CSV
```

## 核心 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/health` | 健康检查 + 当前数据源 |
| GET  | `/api/meta/indicators` | 全部技术指标（含大白话解释） |
| GET  | `/api/meta/factors` | 全部因子 + 绩效指标（含解释） |
| GET  | `/api/meta/strategies` | 可用策略及参数 |
| GET  | `/api/symbols` | 当前数据源下可选标的 |
| GET  | `/api/candles` | OHLCV K 线 |
| POST | `/api/indicators` | 计算指标/因子序列 |
| POST | `/api/backtest` | 运行回测，返回 K 线/指标/净值/成交/绩效 |
| WS   | `/ws/replay` | 模拟实盘：流式推送 bar/signal/portfolio/done |

## 说明

这是一个 **POC / 教学原型**，不构成任何投资建议：市价单、次日开盘成交、单一持仓、结果存内存（无数据库）。目的在于把「数据 → 指标/因子 → 策略 → 虚拟账户 → 绩效」这条链路完整跑通并可视化。
