# StayHub 架构总览

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI (Python 3.12, async) |
| ORM | SQLAlchemy 2.0 + Alembic |
| 数据库 | PostgreSQL 16 |
| 缓存/会话 | Redis 7 |
| 消息队列 | Kafka 7.6 + ZooKeeper |
| 搜索引擎 | Elasticsearch 8.13 (按需启用) |
| 任务队列 | ARQ (Redis 驱动) |
| 前端 | htmx + Alpine.js + Tailwind CSS |
| 部署 | Docker Compose (本地) / systemd (ECS) |

## 项目结构

```
stayhub/
├── backend/          # FastAPI 应用
│   ├── app/
│   │   ├── main.py         # 应用入口
│   │   ├── config.py       # 配置
│   │   ├── database.py     # 数据库连接
│   │   ├── redis.py        # Redis 连接
│   │   ├── kafka.py        # Kafka 生产/消费
│   │   ├── elasticsearch.py# ES 连接与索引
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── routers/        # API 路由
│   │   ├── services/       # 业务逻辑
│   │   ├── middleware/     # 中间件
│   │   └── tasks/          # ARQ 异步任务
│   ├── tests/              # pytest 测试
│   └── alembic/            # 数据库迁移
├── frontend/         # 静态前端文件
├── docker/           # Docker 配置
└── docs/             # 文档
```

## 模块划分

| 路由前缀 | 模块 | 说明 |
|---|---|---|
| /auth | 认证 | 注册/登录/Token 刷新 |
| /users | 用户 | 用户资料 |
| /listings | 房源 | 房源 CRUD/审核/图片 |
| /search | 搜索 | 关键词/地理搜索 |
| /bookings | 预订 | 预订状态机 |
| /payments | 支付 | 支付/分账/退款 |
| /reviews | 评价 | 评价/回复 |
| /messages | 消息 | 会话/消息/WebSocket |
| /social | 社交 | 笔记/评论/点赞/关注 |
| /admin | 管理 | 运营管理 |
| /ai | AI | 聊天/DeepSeek 代理 |
