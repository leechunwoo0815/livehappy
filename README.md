# LiveHappy — 开心住酒店民宿预订平台

[![Python CI](https://github.com/leechunwoo0815/livehappy/actions/workflows/python-ci.yml/badge.svg)](https://github.com/leechunwoo0815/livehappy/actions/workflows/python-ci.yml)

FastAPI + PostgreSQL + Redis + Kafka 全栈单体应用。前端使用 Open Design 精美原型 + htmx 动态绑定。

## 项目状态

```
✅ 所有功能模块开发完成      ✅ 31 个 API 端点
✅ 15 单元测试全部通过       ✅ Ruff 零错误
✅ GitHub Actions CI 通过    ✅ 亮/暗双主题
✅ Docker Compose 就绪       ✅ 阿里云 ECS 部署方案就绪
```

## 快速启动

```bash
# 一键启动全部 18 个容器（后端 + 前端 + 中间件）
docker compose -f docker/docker-compose.yml up -d --build

# 访问
#   前端页面:  http://localhost:3000
#   API 接口:  http://localhost:8000/api/
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI (Python 3.12, async) |
| 数据库 | PostgreSQL 16 + SQLAlchemy 2.0 + Alembic |
| 缓存/队列 | Redis 7 (ARQ 任务队列) |
| 消息 | Kafka 7.6 + ZooKeeper |
| 搜索引擎 | Elasticsearch 8.13 (按需启用) |
| 前端 | 纯 HTML + htmx + Alpine.js |
| 设计系统 | 自定义 system.css (26KB, CSS 变量, 亮/暗) |
| 部署 | Docker Compose / 阿里云 ECS systemd |

## 项目结构

```
backend/                  # FastAPI 后端
├── app/
│   ├── main.py           # 入口, 8 路由模块, /api 前缀
│   ├── config.py         # pydantic-settings 配置
│   ├── database.py       # async SQLAlchemy + asyncpg
│   ├── redis.py          # Redis 连接池
│   ├── kafka.py          # aiokafka 生产者
│   ├── elasticsearch.py  # ES 客户端 (暂禁)
│   ├── models/           # 10 个 ORM 模型
│   ├── schemas/          # Pydantic 请求/响应体
│   ├── routers/          # 8 个路由文件, 31 端点
│   ├── services/         # 业务逻辑层
│   ├── middleware/       # JWT 认证
│   └── tasks/            # ARQ 异步任务
├── tests/                # 15 测试
└── alembic/              # 数据库迁移

frontend/                 # 前端静态文件
├── index.html            # 首页（完整版页面）
├── css/system.css        # 设计系统
├── js/
│   ├── htmx.min.js       # API 数据绑定
│   ├── alpine.min.js     # 前端交互
│   └── app.js            # 主题切换持久化
├── screens/              # 20+ 页面
│   ├── auth/             # 登录 / 注册
│   ├── listings/         # 搜索 / 详情 / 创建
│   ├── bookings/         # 列表 / 详情 / 确认
│   ├── messages/         # 会话 / 聊天
│   ├── social/           # 动态 / 笔记
│   ├── reviews/          # 评价
│   ├── users/            # 个人中心
│   ├── admin/            # 管理后台
│   └── ai/               # AI 助手
├── nginx.conf            # /api 反代到后端
└── Dockerfile            # nginx:alpine

docker/
├── docker-compose.yml    # 18 容器编排
└── Dockerfile.backend    # Python 多阶段构建
```

## API 概览

所有接口以 `/api` 开头，Nginx 反向代理到后端 8000 端口。

| 方法 | 路径 | 模块 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register` | 认证 | 注册新用户 |
| POST | `/api/auth/login` | 认证 | 登录获取 Token |
| POST | `/api/auth/refresh` | 认证 | 刷新 JWT |
| GET | `/api/users/me` | 用户 | 当前用户资料 |
| GET | `/api/listings/search` | 房源 | 搜索房源 (城市/价格/人数) |
| GET | `/api/listings/{id}` | 房源 | 房源详情 + 图片 |
| POST | `/api/listings/` | 房源 | 创建房源 |
| PUT | `/api/listings/{id}` | 房源 | 更新房源 |
| DELETE | `/api/listings/{id}` | 房源 | 删除房源 |
| POST | `/api/listings/{id}/approve` | 房源 | 审核通过/拒绝 |
| POST | `/api/listings/{id}/photos` | 房源 | 添加照片 |
| GET | `/api/listings/{id}/photos` | 房源 | 照片列表 |
| POST | `/api/bookings/` | 预订 | 创建预订 |
| GET | `/api/bookings/` | 预订 | 我的预订列表 |
| POST | `/api/bookings/{id}/pay` | 预订 | 支付 (10% 平台费) |
| POST | `/api/bookings/{id}/cancel` | 预订 | 取消/退款 |
| POST | `/api/messages/send` | 消息 | 发送消息 |
| GET | `/api/messages/conversations` | 消息 | 会话列表 |
| GET | `/api/messages/conversations/{id}/messages` | 消息 | 消息列表 |
| POST | `/api/messages/conversations/{id}/read` | 消息 | 标记已读 |
| GET | `/api/social/notes` | 社交 | 笔记列表 |
| POST | `/api/social/notes` | 社交 | 创建笔记 |
| POST | `/api/social/notes/{id}/like` | 社交 | 点赞 (唯一约束) |
| POST | `/api/social/notes/{id}/unlike` | 社交 | 取消点赞 |
| POST | `/api/social/notes/{id}/comments` | 社交 | 评论 |
| POST | `/api/social/follow/{id}` | 社交 | 关注用户 |
| POST | `/api/social/unfollow/{id}` | 社交 | 取消关注 |
| POST | `/api/reviews/` | 评价 | 创建评价 (1-5分) |
| GET | `/api/reviews/listing/{id}` | 评价 | 房源评价列表 |
| POST | `/api/ai/chat` | AI | 聊天 (Mock/DeepSeek) |

## 数据模型

10 个 ORM 模型: User, Listing, ListingPhoto, Booking, Payment, Conversation, Message, Note, NoteComment, NoteLike, UserFollow, Review, ChatMessage

## 开发

```bash
make test        # 15 测试 (SQLite 内存数据库)
make precommit   # ruff format + ruff check + pytest 闭环
make dc-up       # Docker Compose 启动全部

# 本地开发（只容器化中间件）
docker compose -f docker/docker-compose.yml up -d postgres redis kafka
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

## CI/CD

- **Python CI** (GitHub Actions): push/PR 到 develop 分支触发
  - Ruff lint → Ruff format check → pytest
  - 缓存 pip 依赖加速
- **Deploy**: 推送到 main 分支或 v* tag 时构建 Docker 镜像推送到阿里云 ACR

## 部署

- **本地**: `docker compose -f docker/docker-compose.yml up -d --build`
- **阿里云 ECS**: 见 `docs/03-deployment/02-ecs-deploy.md`
