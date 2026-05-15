.PHONY: dev test lint format dc-up dc-down dc-build clean precommit

dev: ## 本地启动后端
	uv run uvicorn app.main:app --reload --port 8000

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

dc-up: ## Docker Compose 启动全部
	docker compose -f docker/docker-compose.yml up -d --build

dc-down: ## Docker Compose 停止全部
	docker compose -f docker/docker-compose.yml down

dc-build: ## Docker Compose 构建
	docker compose -f docker/docker-compose.yml build

dc-logs: ## Docker Compose 日志
	docker compose -f docker/docker-compose.yml logs -f

dc-ps: ## Docker Compose 状态
	docker compose -f docker/docker-compose.yml ps

clean: ## 清理
	rm -rf backend/**/__pycache__ backend/.pytest_cache .pytest_cache

help: ## 帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
