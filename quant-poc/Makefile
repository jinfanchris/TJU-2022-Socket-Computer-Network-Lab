# Quant Trading POC — developer tasks.
# Usage: `make help` to list targets. All targets run from the quant-poc/ dir.

PY      ?= python
PORT    ?= 8000
API     ?= http://localhost:$(PORT)
DATA    ?= synthetic

.DEFAULT_GOAL := help

.PHONY: help install install-data backend web web-build tui \
        test test-web test-all sample-csv clean

help: ## 显示可用命令
	@echo "Quant Trading POC — make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "变量: PORT=$(PORT) DATA=$(DATA) (可覆盖，如 make backend DATA=yfinance PORT=9000)"

install: ## 安装后端(Python)+ 前端(npm)依赖
	$(PY) -m pip install -r requirements.txt
	cd web && npm install

install-data: ## 安装真实行情可选依赖 (yfinance, ccxt)
	$(PY) -m pip install yfinance ccxt

backend: ## 启动 FastAPI 引擎 (REST + WebSocket)
	QUANT_DATA_MODE=$(DATA) uvicorn quantpoc.api.app:app --reload --port $(PORT)

web: ## 启动 React 网页开发服务器 (Vite, :5173)
	cd web && npm run dev

tui: ## 启动 Textual 终端界面 (需后端已运行)
	$(PY) -m tui.app --api $(API)

test: ## 运行后端端到端测试 (pytest, 合成数据, 无需联网)
	$(PY) -m pytest -q

test-web: ## 前端类型检查 + 构建 (tsc + vite build)
	cd web && npm run build

test-all: test test-web ## 运行全部测试(后端 + 前端)

sample-csv: ## 重新生成内置示例 CSV (data/samples/AAPL.csv)
	$(PY) -c "from quantpoc.data.synthetic import SyntheticDataSource as S; \
d=S(seed=7).history('SYNTH-BULL', limit=500).round(2); \
d.to_csv('data/samples/AAPL.csv', index_label='date'); \
print('wrote data/samples/AAPL.csv', d.shape)"

clean: ## 清理缓存 / 构建产物 (__pycache__, dist, node_modules)
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf web/dist web/node_modules .pytest_cache
	@echo "cleaned."
