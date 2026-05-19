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

# 创建数据库和用户
createuser -s stayhub
createdb -O stayhub stayhub
psql -c "ALTER USER stayhub WITH PASSWORD 'devpassword';"
```

## 一键启动

```bash
./run.sh
```

脚本自动执行: 创建虚拟环境 → 安装依赖 → 运行迁移 → 启动后端 :8001 → 启动前端 :3001。

## 手动启动

```bash
# 设置环境变量
export DATABASE_URL=postgresql+asyncpg://stayhub:devpassword@localhost:5432/stayhub
export JWT_SECRET_KEY=dev-secret-key-change-in-production
export DEBUG=true

# 运行迁移
cd backend && alembic upgrade head

# 启动后端 (热重载)
PYTHONPATH=. uvicorn app.main:app --reload --port 8001

# 另一个终端: 启动前端
python3 -m http.server 3001 -d ../frontend/
```

## 访问

| 服务 | 地址 |
|---|---|
| 后端 API | http://localhost:8001 |
| Swagger 文档 | http://localhost:8001/docs |
| 健康检查 | http://localhost:8001/health |
| 前端 | http://localhost:3001 |
| PostgreSQL | localhost:5432 |
| Redis (可选) | localhost:6379 |

## 初始数据

```bash
cd backend && python3 scripts/seed.py
```

| 邮箱 | 密码 | 角色 |
|---|---|---|
| admin@test.com | admin123 | 管理员 |
| zhangming@test.com | test123 | 房东 |
| liuyang@test.com | test123 | 普通用户 |

## 测试

```bash
pytest backend/ -q
# 69 tests 全部通过

# 带覆盖率
pytest backend/ -q --cov=backend/app --cov-fail-under=60
```

## Redis 说明

Redis 为可选依赖。如果本机没有安装 Redis，启动时会输出:

```
⚠ Redis unavailable — using in-memory fallback
```

所有 Redis 功能 (速率限制、token 黑名单、token 存储) 通过内存字典自动降级，功能完全不受影响。

## 环境变量

参考 `.env` 文件:

```
DATABASE_URL=postgresql+asyncpg://stayhub:devpassword@localhost:5432/stayhub
JWT_SECRET_KEY=dev-secret-key-change-in-production
DEBUG=true
CORS_ORIGINS=["http://localhost:3001"]
```

## 常见问题

### 端口被占用

```bash
# 查看占用 8001 端口的进程
lsof -i :8001
# 修改 run.sh 中的端口号
```

### 数据库连接失败

确保 PostgreSQL 正在运行并已创建数据库:

```bash
brew services list | grep postgresql
psql -d stayhub -c "SELECT 1"
```
