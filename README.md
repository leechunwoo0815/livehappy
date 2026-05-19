# LiveHappy — 开心住酒店民宿预订平台

FastAPI + PostgreSQL 全栈应用，前端 vanilla JS + 自定义设计系统。**无需 Docker，本地直接运行。**

## 项目状态

```
✅ 106 个测试全部通过          ✅ P0 + P1 功能完成
✅ 20+ 页面 vanilla JS          ✅ E2E 全流程模拟（旅客/房东/管理员）
✅ 前后端一体化                 ✅ 种子数据覆盖全部 16 张表
```

## 快速启动

```bash
# 1. 确保 PostgreSQL 已启动
brew services start postgresql@14

# 2. 创建数据库（首次）
createdb stayhub

# 3. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 DATABASE_URL 和 JWT_SECRET_KEY

# 4. 一键启动
./run.sh

# 访问: http://localhost:8001
# API 文档: http://localhost:8001/docs

# 5. 生成种子数据（可选）
DATABASE_URL="postgresql+asyncpg://你的用户名@localhost:5432/stayhub" \
  PYTHONPATH=backend python backend/scripts/seed.py
```

> Redis 为可选依赖 — 不可用时自动降级为内存存储，无需安装。

## 测试账号（种子数据）

| 邮箱 | 密码 | 角色 |
|---|---|---|
| admin@livehappy.com | admin123 | 管理员 |
| zhangming@livehappy.com | host123 | 房东 |
| liuyang@livehappy.com | user123 | 旅客 |

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI (Python 3.12+, async) |
| 数据库 | PostgreSQL 14+ / SQLite（测试） + SQLAlchemy 2.0 + Alembic |
| 缓存 | Redis 7 (可选 — 不可用时自动内存降级) |
| 前端 | 纯 HTML + vanilla JS + 自定义 system.css，由后端 StaticFiles 挂载 |
| 测试 | pytest + pytest-asyncio + httpx (106 个测试) |
| 代码质量 | Ruff (lint + format) |

## 项目结构

```
backend/
├── app/
│   ├── main.py           # FastAPI 入口，12 路由模块 + 前端 StaticFiles 挂载
│   ├── config.py         # pydantic-settings 配置
│   ├── database.py       # async SQLAlchemy + asyncpg
│   ├── redis.py          # Redis 客户端（带内存降级）
│   ├── models/           # 16 个 ORM 模型
│   ├── schemas/          # Pydantic 请求/响应体
│   ├── routers/          # 12 个路由文件
│   ├── services/         # 业务逻辑层
│   ├── middleware/       # JWT 认证 + 速率限制
│   └── core/             # 异常体系 + 全局处理器
├── scripts/seed.py       # 种子数据（覆盖全部 16 张表）
├── tests/                # 106 个测试
└── alembic/              # 数据库迁移

frontend/
├── index.html            # 首页
├── css/system.css        # 设计系统（亮/暗双主题）
├── js/
│   ├── api-client.js     # API 客户端（自动 refresh token）
│   └── app.js            # translateError / statusLabel / 主题切换
└── screens/              # 20+ 页面
    ├── auth/             # 登录 / 注册
    ├── listings/         # 搜索 / 详情 / 创建
    ├── bookings/         # 列表 / 详情 / 确认
    ├── messages/         # 会话 / 聊天
    ├── social/           # 旅记广场
    ├── users/            # 个人中心
    ├── admin/            # 管理后台
    └── ai/               # AI 助手
```

## API 概览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| **认证** | | |
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/refresh` | 刷新 Token |
| POST | `/api/auth/change-password` | 修改密码 |
| **房源** | | |
| GET | `/api/listings/search` | 搜索（城市/价格/人数/排序） |
| POST/PUT/DELETE | `/api/listings/{id}` | 创建/更新/删除 |
| POST | `/api/listings/{id}/approve` | 审核（管理员） |
| POST | `/api/listings/{id}/favorite` | 收藏/取消收藏 |
| **预订** | | |
| POST | `/api/bookings/` | 创建预订 |
| POST | `/api/bookings/{id}/pay` | 支付（10% 平台费） |
| POST | `/api/bookings/{id}/cancel` | 取消/退款 |
| **消息** | | |
| POST | `/api/messages/send` | 发送消息 |
| GET | `/api/messages/unread-count` | 未读消息数 |
| **社交** | | |
| POST | `/api/social/notes/{id}/like` | 点赞 |
| POST | `/api/social/follow/{id}` | 关注 |
| **评价** | | |
| POST | `/api/reviews/{id}/reply` | 房东回复 |
| **管理** | | |
| GET | `/api/admin/stats` | 仪表盘统计 |
| POST | `/api/admin/users/{id}/ban` | 封禁用户 |
| GET | `/api/admin/audit-logs` | 审计日志 |

## 开发命令

```bash
make test                         # 运行 106 个测试
make lint                         # Ruff lint
make format                       # Ruff 格式化
make precommit                    # format + lint + test
make seed                         # 生成种子数据
```

## 环境变量

参见 `backend/.env.example`。敏感信息（数据库密码、JWT 密钥）通过 `.env` 文件配置，**不要提交到 Git**。

## 许可

MIT
