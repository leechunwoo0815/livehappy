# StayHub — 短租民宿预订平台

Python + FastAPI 重构版，单体应用，全 Docker 部署。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI (Python 3.12, async) |
| 数据库 | PostgreSQL 16 + SQLAlchemy 2.0 |
| 缓存 | Redis 7 |
| 消息队列 | Kafka 7.6 + ZooKeeper |
| 搜索引擎 | Elasticsearch 8.13 (按需启用) |
| 任务队列 | ARQ (Redis 驱动) |
| 前端 | 静态 HTML + htmx (等待模板中) |
| 部署 | Docker Compose / 阿里云 ECS |

## 快速启动

```bash
# 1. 启动中间件 + 后端
docker compose -f docker/docker-compose.yml up -d

# 2. 访问
#    后端 API: http://localhost:8000
#    前端:     http://localhost:3000

# 3. 本地开发（中间件用 Docker，后端用 uvicorn 热重载）
docker compose -f docker/docker-compose.yml up -d postgres redis kafka
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

## 项目结构

```
backend/
├── app/
│   ├── main.py           # FastAPI 入口 + 路由注册
│   ├── config.py         # 配置管理 (pydantic-settings)
│   ├── database.py       # async SQLAlchemy 引擎
│   ├── redis.py          # Redis 连接
│   ├── kafka.py          # Kafka 生产者
│   ├── elasticsearch.py  # ES 客户端 (按需启用)
│   ├── models/           # SQLAlchemy ORM 模型
│   ├── schemas/          # Pydantic 请求/响应
│   ├── routers/          # API 路由 (9 模块)
│   ├── services/         # 业务逻辑
│   └── middleware/       # JWT 认证中间件
├── tests/                # pytest 测试
├── alembic/              # 数据库迁移
└── alembic.ini
```

## API 概览

| 路径 | 模块 | 说明 |
|---|---|---|
| `/auth` | 认证 | 注册/登录/Token 刷新 |
| `/users` | 用户 | 用户资料 |
| `/listings` | 房源 | CRUD + 图片 + 审核 + 搜索 |
| `/bookings` | 预订 | 创建/支付/取消, 状态机 |
| `/messages` | 消息 | 会话列表/发送/已读 |
| `/social` | 社交 | 笔记/评论/点赞去重/关注 |
| `/reviews` | 评价 | 评分 1-5, 带回复 |
| `/ai` | AI | 聊天 Mock / DeepSeek 代理 |
| `/admin` | 管理 | (预留) |

## 开发

```bash
make precommit   # 格式化 → 静态检查 → 测试 (提交前闭环)
make test        # 运行测试 (15 tests)
make dc-up       # Docker Compose 启动
```

## 部署

- **本地**: `docker compose -f docker/docker-compose.yml up -d --build`
- **阿里云 ECS**: 见 `docs/03-deployment/02-ecs-deploy.md`
