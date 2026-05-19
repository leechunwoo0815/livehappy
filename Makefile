.PHONY: dev test lint format clean precommit seed

dev: ## 本地启动后端
	PYTHONPATH=backend uvicorn app.main:app --reload --port 8001

test: ## 运行测试
	pytest backend/ -q

lint: ## 静态检查
	ruff check backend/

format: ## 自动格式化
	ruff format backend/
	ruff check --fix backend/

precommit: ## 提交前质量闭环
	ruff format backend/
	ruff check backend/
	pytest backend/ -q
	@echo "✅ 全部通过"

seed: ## 生成测试数据
	PYTHONPATH=backend python backend/scripts/seed.py

clean: ## 清理
	rm -rf backend/**/__pycache__ backend/.pytest_cache .pytest_cache

help: ## 帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
