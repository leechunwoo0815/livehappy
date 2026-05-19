# 本地开发运行

> 本项目不再使用 Docker，所有服务直接跑在宿主机上。

## 前提

- Python 3.12+
- PostgreSQL 14+ (通过 Homebrew 安装)
- Redis 7 (可选 — 不可用时自动内存降级)

## 启动 PostgreSQL

```bash
brew install postgresql@14
brew services start postgresql@14

# 创建数据库
createdb stayhub
```

## 配置环境变量

```bash
cp .env.example backend/.env
# 编辑 backend/.env，填入你的 DATABASE_URL 和 JWT_SECRET_KEY
```

## 一键启动

```bash
./run.sh
```

脚本自动执行: 创建虚拟环境 → 安装依赖 → 运行迁移 → 启动后端 :8001（同时服务前端）。

## 手动启动

```bash
cd backend
source .venv/bin/activate  # 或 python3 -m venv .venv && pip install -e .
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. uvicorn app.main:app --reload --port 8001
```

## 访问

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost:8001 |
| API 文档 | http://localhost:8001/docs |
| 健康检查 | http://localhost:8001/health |

## 种子数据

```bash
DATABASE_URL="postgresql+asyncpg://你的用户名@localhost:5432/stayhub" \
  PYTHONPATH=backend python backend/scripts/seed.py
```

| 邮箱 | 密码 | 角色 |
|---|---|---|
| admin@livehappy.com | admin123 | 管理员 |
| zhangming@livehappy.com | host123 | 房东 |
| liuyang@livehappy.com | user123 | 旅客 |

## 测试

```bash
pytest backend/ -q
# 106 tests 全部通过
```

## Redis 说明

Redis 为可选依赖。如果本机没有安装 Redis，启动时会输出:

```
⚠ Redis unavailable — using in-memory fallback
```

所有 Redis 功能 (速率限制、token 黑名单) 通过内存字典自动降级，功能完全不受影响。

## 环境变量

参见 `.env.example`。敏感信息（数据库密码、JWT 密钥）通过 `.env` 文件配置，**不要提交到 Git**。

## 常见问题

### 端口被占用

```bash
lsof -i :8001
```

### 数据库连接失败

确保 PostgreSQL 正在运行并已创建数据库:

```bash
brew services list | grep postgresql
psql -d stayhub -c "SELECT 1"
```
