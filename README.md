# LiveHappy — 开心住酒店民宿预订平台

FastAPI + PostgreSQL 全栈应用，前端 vanilla JS + 自定义设计系统。**无需 Docker，本地直接运行。**

## 项目状态

```
✅ Phase 0-7 全部完成         🔄 Phase 8-13 全量重构进行中
✅ 21 页面 vanilla JS          ✅ 69 个测试
✅ 本地直接运行               ✅ 阿里云 ECS 部署方案就绪
```

> 重构计划详见 `docs/00-architecture/04-refactor-plan.md`

## 快速启动

```bash
# 1. 确保 PostgreSQL 已启动
brew services start postgresql@14

# 2. 一键启动前后端
./run.sh

# 前端:  http://localhost:3001
# API:   http://localhost:8001/docs
```

## 手动启动

```bash
# 后端
cd backend
PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://stayhub:devpassword@localhost:5432/stayhub JWT_SECRET_KEY=dev-secret-key-change-in-production alembic upgrade head
PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://stayhub:devpassword@localhost:5432/stayhub JWT_SECRET_KEY=dev-secret-key-change-in-production uvicorn app.main:app --reload --port 8001

# 前端
python3 -m http.server 3001 -d ../frontend/
```

> Redis 为可选依赖 — 不可用时自动降级为内存存储，无需安装。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI (Python 3.13, async) |
| 数据库 | PostgreSQL 14 + SQLAlchemy 2.0 + Alembic |
| 缓存 | Redis 7 (可选 — 不可用时自动内存降级) |
| 搜索引擎 | Elasticsearch (按需启用) |
| 前端 | 纯 HTML + vanilla JS + 自定义 system.css |
| 设计系统 | 自定义 system.css (26KB, CSS 变量, 亮/暗) |
| 部署 | 本地直接运行 / 阿里云 ECS systemd |

## 项目结构

```
backend/                  # FastAPI 后端
├── app/
│   ├── main.py           # 入口, 11 路由模块, /api 前缀
│   ├── config.py         # pydantic-settings (env-only secrets)
│   ├── database.py       # async SQLAlchemy + asyncpg
│   ├── redis.py          # Redis 连接池 (带内存降级)
│   ├── elasticsearch.py  # ES 客户端 (按需启用)
│   ├── models/           # 15 个 ORM 模型
│   ├── schemas/          # Pydantic 请求/响应体
│   ├── routers/          # 11 个路由文件
│   ├── services/         # 业务逻辑层
│   ├── middleware/       # JWT 认证 + 速率限制
│   └── tasks/            # ARQ 异步任务
├── tests/                # 69 个测试 (覆盖所有模块)
└── alembic/              # 数据库迁移

frontend/                 # 前端静态文件
├── index.html            # 首页
├── css/system.css        # 设计系统
├── js/
│   ├── api-client.js     # API 客户端 (自动刷新 token)
│   └── app.js            # JWT auth + 主题切换 + nav 渲染
├── screens/              # 21 个页面
│   ├── auth/             # 登录 / 注册
│   ├── listings/         # 搜索 / 详情 / 创建
│   ├── bookings/         # 列表 / 详情 / 确认
│   ├── messages/         # 会话 / 聊天
│   ├── social/           # 动态 / 笔记
│   ├── reviews/          # 评价
│   ├── users/            # 个人中心
│   ├── admin/            # 管理后台 (含审计日志)
│   └── ai/               # AI 助手
└── nginx.conf            # 仅供部署参考 (本地无需 nginx)

scripts/
├── deploy-ecs.sh         # ECS 部署脚本 (含 migration)
├── seed.py               # 测试数据生成器
└── backup.sh             # 数据库备份脚本

run.sh                    # 一键本地启动
```

## API 概览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 (DB + Redis) |
| **认证** | | |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/refresh` | 刷新 Token |
| **用户** | | |
| GET | `/api/users/me` | 当前用户资料 |
| **房源** | | |
| GET | `/api/listings/search` | 搜索 (城市/价格/人数) |
| GET/POST/PUT/DELETE | `/api/listings/{id}` | CRUD |
| POST | `/api/listings/{id}/approve` | 审核 (仅 admin) |
| GET/POST/DELETE | `/api/listings/{id}/photos` | 照片 |
| **预订** | | |
| POST | `/api/bookings/` | 创建 |
| GET | `/api/bookings/` | 列表 |
| POST | `/api/bookings/{id}/pay` | 支付 |
| POST | `/api/bookings/{id}/cancel` | 取消 |
| **消息** | | |
| GET/POST | `/api/messages/conversations` | 会话 |
| GET | `/api/messages/conversations/{id}/messages` | 消息列表 |
| POST | `/api/messages/send` | 发送 |
| POST | `/api/messages/conversations/{id}/read` | 已读 |
| WS | `/api/messages/ws?token=` | WebSocket 实时消息 |
| **社交** | | |
| GET/POST | `/api/social/notes` | 笔记列表/创建 |
| GET | `/api/social/notes/{id}` | 笔记详情 |
| POST | `/api/social/notes/{id}/like\|unlike` | 点赞/取消 |
| GET/POST | `/api/social/notes/{id}/comments` | 评论列表/创建 |
| POST | `/api/social/follow\|unfollow/{id}` | 关注/取消 |
| **评价** | | |
| POST | `/api/reviews/` | 创建评价 |
| GET | `/api/reviews/listing/{id}` | 房源评价列表 |
| **AI** | | |
| POST | `/api/ai/chat` | 聊天 (Mock/DeepSeek) |
| **管理** | | |
| GET | `/api/admin/stats` | 仪表盘统计数据 |
| GET | `/api/admin/listings` | 房源管理列表 |
| GET | `/api/admin/listings/pending` | 待审核房源 |
| POST | `/api/admin/listings/{id}/offline` | 下架房源 |
| GET | `/api/admin/users` | 用户管理列表 |
| POST | `/api/admin/users/{id}/ban\|unban` | 封禁/解封 |
| PUT | `/api/admin/users/{id}/role` | 修改角色 |
| GET | `/api/admin/bookings` | 订单管理 |
| GET | `/api/admin/audit-logs` | 审计日志 |
| **上传** | | |
| POST | `/api/upload` | 文件上传 |

## 数据模型

15 个 ORM 模型: User, Listing, ListingPhoto, Booking, Payment, Conversation, Message, Note, NoteComment, NoteLike, UserFollow, Review, ChatMessage, AuditLog, Notification

## 开发

```bash
ruff format backend/ && ruff check backend/ && pytest backend/ -q
```

## CI/CD

```bash
ruff format backend/  && ruff check backend/  && \
pytest backend/ -q --cov=backend/app --cov-fail-under=60
```

## 部署

- **本地**: `./run.sh`
- **阿里云 ECS**: 见 `docs/03-deployment/02-ecs-deploy.md`

## 管理员账号

| 邮箱 | 密码 | 角色 |
|---|---|---|
| admin@test.com | admin123 | 管理员 |
| zhangming@test.com | test123 | 房东 |
| liuyang@test.com | test123 | 普通用户 |
