# 开发工作流

## 本地开发

```bash
# 1. 启动中间件
docker compose -f docker/docker-compose.yml up -d postgres redis kafka

# 2. 启动后端 (热重载)
cd backend && uv run uvicorn app.main:app --reload --port 8000

# 3. 测试
pytest backend/ -q
```

## 代码质量闭环

每次提交前必须执行:

```bash
make precommit
```

等价于:

```bash
ruff format backend/    # 自动格式化
ruff check backend/     # 静态检查
pytest backend/ -q      # 测试
```

## Git 分支策略

- `develop` — 日常开发，CI 自动检查
- `main` — 稳定版本，触发部署

## CI Pipeline

GitHub Actions (`python-ci.yml`):
1. Ruff lint + format check
2. pytest 单元测试

## 部署流程

1. 合并到 main 分支
2. CI 构建 Docker 镜像推送到阿里云 ACR
3. ECS 上拉取镜像或用 systemd 运行
