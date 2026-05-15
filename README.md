# LiveHappy — 开心住酒店民宿预订平台

Python + FastAPI 重构版，前端使用 Open Design 精美原型 + htmx。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI (Python 3.12, async) |
| 数据库 | PostgreSQL 16 + SQLAlchemy 2.0 |
| 缓存 | Redis 7 |
| 消息队列 | Kafka 7.6 + ZooKeeper |
| 前端 | 纯 HTML + htmx + Alpine.js |
| 设计系统 | 自定义 system.css (26KB, 亮/暗双主题) |
| 部署 | Docker Compose / 阿里云 ECS |

## 快速启动

```bash
# 一键启动全部
docker compose -f docker/docker-compose.yml up -d --build

# 访问
#   前端页面:  http://localhost:3000
#   API 接口:  http://localhost:8000/api/
```

## 项目结构

```
backend/                  # FastAPI 后端
├── app/
│   ├── main.py           # 入口 (8 路由模块, /api 前缀)
│   ├── models/           # 9 个 ORM 模型
│   ├── routers/          # 8 个路由模块
│   ├── services/         # 业务逻辑
│   └── ...
├── tests/                # 15 测试
└── ...

frontend/                 # 前端静态文件
├── index.html            # 首页（完整版模板）
├── css/system.css        # 设计系统
├── js/
│   ├── htmx.min.js       # API 数据绑定
│   ├── alpine.min.js     # 前端交互
│   └── app.js            # 主题切换
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

docker/docker-compose.yml # 18 容器编排
```

## API 概览

所有接口以 `/api` 开头，前端 nginx 反代。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/refresh` | 刷新 Token |
| GET | `/api/listings/search` | 搜索房源 |
| GET/POST/PUT/DELETE | `/api/listings/{id}` | 房源 CRUD |
| POST | `/api/bookings/` | 创建预订 |
| POST | `/api/bookings/{id}/pay` | 支付 |
| POST | `/api/bookings/{id}/cancel` | 取消 |
| POST | `/api/messages/send` | 发送消息 |
| POST | `/api/ai/chat` | AI 聊天 |
| POST | `/api/social/notes` | 社交笔记 |
| POST | `/api/reviews/` | 评价 |

## 开发

```bash
make test        # 15 测试
make dc-up       # Docker 启动
make precommit   # ruff → pytest 闭环
```
