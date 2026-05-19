# LiveHappy — 开心住酒店民宿预订平台

> 面向旅客和房东的在线住宿预订平台，支持房源发布、在线预订、支付结算、站内消息、社交笔记和 AI 助手功能。

---

## 1. 项目概述

**项目名称**：LiveHappy（开心住）
**一句话定位**：面向 C 端的酒店/民宿在线预订平台，为旅客提供便捷的住宿预订，为房东提供房源管理与收益结算。
**目标用户**：旅客（预订住宿）、房东（发布和管理房源）、平台运营人员（审核房源、管理用户）
**核心价值**：让旅客快速找到理想房源并完成预订，让房东高效管理房源和收益。

### 业务域划分

| 域 | 职责 | 核心实体 | 对应路由 |
|---|---|---|---|
| 认证域 | 注册/登录/Token刷新/封禁 | User | `/api/auth` |
| 用户域 | 个人资料/头像 | User | `/api/users` |
| 房源域 | 发布/审核/搜索/展示/照片 | Listing, ListingPhoto | `/api/listings` |
| 交易域 | 预订/支付(10%平台费)/退款 | Booking, Payment | `/api/bookings` |
| 消息域 | 站内信/会话/已读状态 | Conversation, Message | `/api/messages` |
| 社交域 | 笔记/评论/点赞/关注 | Note, NoteComment, NoteLike, UserFollow | `/api/social` |
| 评价域 | 评分(1-5分)/房东回复 | Review | `/api/reviews` |
| 管理域 | 后台统计/房源审核/用户管理/操作日志 | AuditLog | `/api/admin` |
| 上传域 | 文件上传（图片限制） | — | `/api/upload` |
| AI 域 | 智能客服聊天 | ChatMessage | `/api/ai` |

### 核心业务规则

- 房源状态流转：`pending` → `approved` / `rejected`（由管理员审核）
- 预订状态流转：`pending` → `confirmed`（支付后）→ `completed` / `cancelled`
- 取消已确认的预订会自动触发退款，支付金额归零
- 平台抽佣 10%，`host_payout = total_price - platform_fee`
- 房源搜索支持按城市/价格区间/入住人数筛选，默认分页 20 条/页
- 每个用户对同一笔记只能点赞一次（UniqueConstraint）
- 每个用户对同一房源只能发布一条评价（booking_id 唯一约束）
- 用户角色：`user`（普通用户）/ `host`（房东）/ `admin`（管理员）
- 封禁用户：管理员可封禁用户，被封禁用户的所有请求返回 403
- Token 黑名单：用户登出或被封禁后，JWT JTI 加入 Redis 黑名单

### 业务规则详细

#### 1. 房源域 (Listing)

**状态机：**
```
pending ──(管理员 approve)──→ approved ──(管理员 offline)──→ is_active=false
   │
   └──(管理员 reject)──→ rejected
```

**业务规则：**
- 创建房源后状态为 `pending`，需管理员审核
- `approved` 的房源才能被搜索到、被预订
- 房东只能编辑/删除自己的房源（`host_id` 校验）
- 删除房源是**软删除**（`is_active=False`），不物理删除
- 管理员下架房源（offline）后：**已有的预订继续执行**，只是不能创建新预订
- 照片管理：每个房源可有多张照片，一张标记为 `is_primary`（设为封面时自动取消其他主图）

**关联影响：**
- 房源下架 → 不影响已确认的预订 → 但搜索结果不再显示
- 房源被删除 → 已有预订仍保留（`listing_id` 外键不级联删除）

#### 2. 交易域 (Booking + Payment)

**预订状态机：**
```
pending ──(旅客支付)──→ confirmed ──(退房日期后)──→ completed
   │                        │
   │                        └──(旅客/房东取消)──→ cancelled + 自动退款
   │
   └──(旅客/房东取消)──→ cancelled（无退款，因为未支付）
```

**业务规则：**
- 创建预订时校验：入住 < 退房、不能预订过去日期、房源已审核且活跃、入住人数 ≤ max_guests
- 总价 = `price_per_night × 住宿天数`（Decimal 精确计算）
- 支付时计算：`platform_fee = total_price × 10%`，`host_payout = total_price - platform_fee`
- 取消规则：
  - `pending` 状态取消：直接取消，无退款（未支付）
  - `confirmed` 状态取消：**全部清零**（amount/host_payout/platform_fee 都设为 0），状态改 refunded
  - `completed` 状态：**不可取消**
- 旅客和房东都可以取消预订（`guest_id` 或 `host_id` 校验）
- 预订列表支持按角色查看：`role=guest`（我的订单）或 `role=host`（我的房源订单）

**关联影响：**
- 取消预订 → 自动将 Payment 状态改为 `refunded`，金额全部清零
- 预订完成 → 旅客可以对该预订写评价（status 必须为 `completed`）

#### 3. 评价域 (Review)

**业务规则：**
- **前置条件**：`booking.status == "completed"`（已退房才能评价）（⚠️ 当前代码写的是 `confirmed`，需要修复）
- 每个预订只能评价一次（`booking_id` 唯一约束）
- 评分范围 1-5 分
- 房东可以回复评价（`reply` 字段）
- 评价创建后不可修改

**关联影响：**
- 评价不影响预订状态
- 评价会影响房源的平均评分（未来扩展）

#### 4. 社交域 (Note + Follow)

**笔记业务规则：**
- 任何登录用户都可以创建笔记
- 笔记有 `likes_count` 和 `comments_count` 计数器（冗余字段，增删时同步更新）
- 每个用户对同一笔记只能点赞一次（`UniqueConstraint("note_id", "user_id")`）
- 点赞/取消点赞时自动 +1/-1 计数器
- 评论创建时自动 +1 计数器

**关注业务规则：**
- 不能关注自己
- 每对用户只能关注一次（`UniqueConstraint("follower_id", "following_id")`）
- 关注/取关是单向的（A 关注 B ≠ B 关注 A）

#### 5. 消息域 (Message)

**业务规则：**
- 发送消息时自动查找或创建会话（`_get_or_create_conversation`）
- 会话是两人之间的（`participant_one` + `participant_two`）
- 每个会话有独立的未读计数（`unread_count_one` / `unread_count_two`）
- 标记已读时：将对方发的所有未读消息设为 `is_read=True`，清零自己的未读计数
- 支持 WebSocket 实时推送（`/api/messages/ws`），连接时需传 JWT token

#### 6. 管理域 (Admin)

**权限矩阵：**

| 操作 | user | host | admin |
|---|---|---|---|
| 注册/登录/刷新Token | ✅ | ✅ | ✅ |
| 搜索/查看房源 | ✅ | ✅ | ✅ |
| 创建预订/支付/取消 | ✅ | ✅ | ✅ |
| 发消息/社交/评价 | ✅ | ✅ | ✅ |
| 创建/编辑/删除自己的房源 | ❌ | ✅ | ✅ |
| 查看自己的房东订单 | ❌ | ✅ | ✅ |
| 审核房源（approve/reject） | ❌ | ❌ | ✅ |
| 下架房源 | ❌ | ❌ | ✅ |
| 封禁/解封用户 | ❌ | ❌ | ✅ |
| 修改用户角色 | ❌ | ❌ | ✅ |
| 删除用户 | ❌ | ❌ | ✅ |
| 查看统计数据 | ❌ | ❌ | ✅ |
| 查看审计日志 | ❌ | ❌ | ✅ |
| 生成种子数据 | ❌ | ❌ | ✅ |

**审计日志：** 管理员的所有操作（下架/封禁/解封/角色变更/删除用户）自动记录到 `audit_logs` 表。

#### 7. 认证域 (Auth)

**业务规则：**
- 密码使用 bcrypt 哈希存储，不可逆
- JWT 分两种：`access_token`（30分钟）和 `refresh_token`（7天）
- access_token 包含：`sub`(用户ID)、`exp`(过期)、`type`("access")、`role`("user/host/admin")、`jti`(唯一ID)
- Token 黑名单：`jti` 存入 Redis `blacklist:{jti}`，被拉黑的 Token 无法使用
- 封禁检查：被封禁用户的 ID 存入 Redis `banned_users` 集合
- 登录限流：10次/5分钟/IP（Redis 降级时限流失效）
- 全局 JWT 中间件：解析 Token → 检查黑名单 → 检查封禁 → 注入 `request.state`
- 豁免路径（不需要 Token）：`/api/auth/login`、`/api/auth/register`、`/api/auth/refresh`、`/health`、`/docs` 等

#### 8. AI 域

**业务规则：**
- 需要登录才能使用
- 优先调用 DeepSeek API（需配置 `DEEPSEEK_API_KEY` + `AI_ENABLED=true`）
- 未配置时使用 Mock 随机回复（7条预设回复）
- API 调用失败时自动降级为 Mock 回复
- 每条消息（用户 + AI 回复）都存入 `chat_messages` 表

---

## 2. 快速开始

```bash
# 环境要求
# Python >= 3.12, PostgreSQL 14+ (brew install postgresql@14)
# 不需要 Docker、Redis、Kafka 等外部依赖

# 1. 启动 PostgreSQL
brew services start postgresql@14

# 2. 创建数据库
createdb stayhub

# 3. 一键启动（自动创建 venv、安装依赖、运行迁移、启动前后端）
./run.sh

# 启动后访问：
#    后端 API:  http://localhost:8001
#    前端页面:  http://localhost:3001
#    API 文档:  http://localhost:8001/docs
#    健康检查:  http://localhost:8001/health
```

### run.sh 工作流程

```bash
#!/usr/bin/env bash
# 1. 创建 Python venv（如不存在）
# 2. 安装依赖
# 3. 运行 alembic upgrade head
# 4. 启动后端 uvicorn --port 8001 --reload
# 5. 启动前端 python3 -m http.server 3001 -d frontend/
# Ctrl+C 同时停止前后端
```

### 开发模式手动启动

```bash
# 后端
source backend/.venv/bin/activate
PYTHONPATH=backend uvicorn app.main:app --reload --port 8001

# 前端（纯静态文件，无需构建）
python3 -m http.server 3001 -d frontend/
```

### Redis 说明

Redis **完全可选**。项目使用 `_InMemoryRedis` 内存替代实现：
- 连不上 Redis 自动降级，零外部依赖
- 降级后限流和 Token 黑名单功能失效，其他功能正常
- 生产环境建议启用 Redis 以支持限流和黑名单

---

## 3. 技术栈

| 层 | 技术 | 版本 | 备注 |
|---|---|---|---|
| 语言 | Python | 3.12+ | 全链路 async/await 异步 |
| Web 框架 | FastAPI | >= 0.115 | 自动生成 OpenAPI 文档 |
| ORM | SQLAlchemy | >= 2.0 | async 模式 (AsyncSession + asyncpg) |
| 数据库 | PostgreSQL | 14+ | 本地 brew 安装，asyncpg 驱动 |
| 迁移工具 | Alembic | >= 1.14 | schema 变更必须生成迁移文件 |
| 缓存 | Redis（可选） | 7 | 内存降级替代，不影响启动 |
| 搜索引擎 | Elasticsearch | 8.13 | 按需启用 (elasticsearch_enabled=false) |
| 前端 | vanilla JS + api-client.js | — | 纯 HTML 静态文件，python3 -m http.server |
| 设计系统 | system.css | — | CSS 变量，亮/暗双主题 |
| 监控 | Sentry | — | 错误追踪（需 SENTRY_DSN） |
| CI/CD | GitHub Actions | — | push/PR 到 develop 触发 |
| 代码质量 | Ruff | >= 0.8 | lint + format |
| 测试 | pytest + pytest-asyncio | >= 8.3 | 异步测试，SQLite 内存数据库 |
| HTTP 客户端 | httpx | >= 0.28 | 测试用 ASGITransport |
| 配置管理 | pydantic-settings | >= 2.7 | .env 文件 + 环境变量 |
| 认证 | python-jose + bcrypt | — | JWT (HS256) + 密码哈希 |

---

## 4. 项目结构

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口，11 个路由模块注册
│   │   ├── config.py            # pydantic-settings 配置类 + model_validator
│   │   ├── database.py          # async SQLAlchemy 引擎 + get_db 依赖注入
│   │   ├── redis.py             # Redis 客户端 + _InMemoryRedis 降级实现
│   │   ├── elasticsearch.py     # ES 客户端 (按需启用)
│   │   ├── core/                # 核心基础设施
│   │   │   ├── exceptions.py    # 自定义异常体系 (AppException 基类)
│   │   │   └── handlers.py      # 全局异常处理器 → 统一 BaseResponse
│   │   ├── models/              # ORM 模型
│   │   │   ├── base.py          # Base + TimestampMixin
│   │   │   ├── user.py          # User
│   │   │   ├── listing.py       # Listing + ListingPhoto
│   │   │   ├── booking.py       # Booking + Payment
│   │   │   ├── message.py       # Conversation + Message
│   │   │   ├── social.py        # Note + NoteComment + NoteLike + UserFollow
│   │   │   ├── review.py        # Review
│   │   │   ├── chat.py          # ChatMessage
│   │   │   └── audit_log.py     # AuditLog（管理员操作日志）
│   │   ├── schemas/             # Pydantic 请求/响应 Schema
│   │   │   ├── common.py        # BaseResponse / PaginatedData 统一响应格式
│   │   │   ├── auth.py          # RegisterRequest / LoginRequest / TokenResponse
│   │   │   ├── booking.py       # BookingCreate / BookingResponse / PaymentResponse
│   │   │   ├── listing.py       # ListingCreate / ListingUpdate / ListingResponse
│   │   │   ├── message.py       # MessageSend / ConversationResponse
│   │   │   └── user.py          # UserResponse / UserUpdate
│   │   ├── routers/             # API 路由（11 个模块）
│   │   │   ├── auth.py          # 注册/登录/刷新Token
│   │   │   ├── users.py         # 当前用户资料
│   │   │   ├── listings.py      # 房源 CRUD + 搜索 + 审核 + 照片
│   │   │   ├── bookings.py      # 预订/支付/取消/列表
│   │   │   ├── messages.py      # 发送消息/会话列表/消息列表/已读
│   │   │   ├── social.py        # 笔记/评论/点赞/关注
│   │   │   ├── reviews.py       # 评价创建/查询
│   │   │   ├── admin.py         # 后台管理（统计/审核/封禁/操作日志）
│   │   │   ├── upload.py        # 文件上传（图片限制）
│   │   │   ├── health.py        # 健康检查（DB + Redis 状态）
│   │   │   └── ai.py            # AI 聊天
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── admin.py         # 管理后台（统计/审核/封禁/审计日志）
│   │   │   ├── auth.py          # 密码哈希/JWT 生成
│   │   │   ├── booking.py       # 预订/支付/退款/列表
│   │   │   ├── listing.py       # 房源 CRUD/搜索/审核
│   │   │   ├── listing_photo.py # 照片管理
│   │   │   ├── message.py       # 消息/会话管理
│   │   │   ├── review.py        # 评价创建/查询
│   │   │   ├── social.py        # 笔记/评论/点赞/关注
│   │   │   ├── user.py          # 用户查询（get_by_id/get_by_email）
│   │   │   └── ai.py            # AI 聊天
│   │   ├── middleware/          # 中间件
│   │   │   ├── auth.py          # JWTMiddleware (全局) + get_current_user (依赖项)
│   │   │   └── ratelimit.py     # 请求限流中间件 (Redis 降级时跳过)
│   │   └── tasks/               # ARQ 异步任务
│   │       └── __init__.py      # (待扩展)
│   ├── scripts/
│   │   └── seed.py              # 测试数据生成脚本
│   ├── tests/                   # 测试
│   │   ├── conftest.py          # 测试配置：SQLite 内存 DB + 依赖覆盖
│   │   ├── test_auth.py         # 认证测试
│   │   ├── test_bookings.py     # 预订测试
│   │   ├── test_listings.py     # 房源测试
│   │   └── test_root.py         # 根路由测试
│   └── alembic/                 # 数据库迁移
├── frontend/
│   ├── index.html               # 首页
│   ├── css/system.css           # 设计系统（亮/暗双主题）
│   ├── js/                      # api-client.js + app.js（无第三方依赖）
│   └── screens/                 # 20+ 页面（auth/listings/bookings/...）
├── uploads/                     # 用户上传文件存储目录
├── scripts/                     # 运维脚本
├── docs/                        # 项目文档
├── .github/workflows/           # CI/CD (Ruff + pytest)
├── 网站原型设计模板/              # 设计稿
├── CLAUDE.md                    # ← 本文件
├── run.sh                       # 一键启动脚本（本地开发）
├── pyproject.toml               # 项目配置 + 依赖
├── Makefile                     # 常用命令
├── .env.example                 # 环境变量模板
└── .editorconfig                # 编辑器配置
```

### 各目录职责边界

| 目录 | 允许做的事 | 禁止做的事 |
|---|---|---|
| `core/` | 异常体系、全局处理器、公共工具 | 放业务逻辑、数据库操作 |
| `models/` | 定义 ORM 模型、表关系、约束 | 放业务逻辑、HTTP 处理 |
| `schemas/` | Pydantic 请求/响应 Schema、字段校验 | 放 ORM 查询、数据库操作 |
| `routers/` | 接收请求、参数校验、调用 service、返回响应 | 放复杂业务逻辑（超过 20 行必须下沉） |
| `services/` | 业务逻辑、事务编排、跨表操作 | 直接操作 Request/Response 对象 |
| `middleware/` | 认证/JWT/限流/日志 | 放业务逻辑 |
| `tasks/` | ARQ 异步任务（邮件/通知等） | 同步阻塞操作 |
| `tests/` | 单元测试、集成测试 | 放生产代码 |
| `scripts/` | 数据种子/运维脚本 | 放应用代码 |

### 数据模型关系

```
User (1) ──── (*) Listing          # 房东发布房源
User (1) ──── (*) Booking          # 旅客创建预订
Listing (1) ── (*) Booking         # 房源关联多个预订
Listing (1) ── (*) ListingPhoto    # 房源有多张照片
Booking (1) ── (1) Payment         # 预订对应一笔支付
Booking (1) ── (1) Review          # 预订对应一条评价
Conversation (1) ── (*) Message    # 会话包含多条消息
Note (1) ──── (*) NoteComment      # 笔记有多个评论
Note (1) ──── (*) NoteLike         # 笔记有多个点赞
User (1) ──── (*) UserFollow       # 用户关注关系
Admin (1) ── (*) AuditLog          # 管理员操作日志
```

---

## 5. 架构约束

### 分层依赖规则（单向，不可逆）

```
Router (接收请求)
  │
  ▼
Service (业务逻辑)
  │
  ▼
Model (数据访问)  ←── Schema (仅用于类型定义)
       │
       ▼
  core/exceptions.py  ← 所有业务异常的基类
```

- ✅ Router 通过 `Depends(get_current_user)` 获取认证用户 ID，传给 Service
- ✅ Service 接收 `AsyncSession` + 业务参数，抛出自定义异常（`AppException` 子类）
- ✅ 全局异常处理器自动将异常转换为统一 `BaseResponse` 格式
- ❌ Router 直接执行 `select()` 查询（必须调用 Service）
- ❌ Service 直接使用 `HTTPException`（应使用 `AppException` 子类）
- ❌ Model 导入 Service 或 Router（单向依赖）

### 统一响应格式

```json
// 成功响应
{
  "success": true,
  "data": { ... },
  "message": null,
  "code": null
}

// 错误响应
{
  "success": false,
  "data": null,
  "message": "资源不存在",
  "code": "NOT_FOUND"
}
```

### 自定义异常体系

```python
# core/exceptions.py - 所有业务异常继承 AppException
class AppException(Exception):
    """基类，全局异常处理器自动捕获"""
    def __init__(self, message: str, code: str, status_code: int): ...

class NotFoundException(AppException):    # 404 NOT_FOUND
class ForbiddenException(AppException):   # 403 FORBIDDEN
class ConflictException(AppException):    # 409 CONFLICT
class BadRequestException(AppException):  # 400 BAD_REQUEST
class UnauthorizedException(AppException):# 401 UNAUTHORIZED
```

### 中间件执行顺序

```
请求进入 → CORS → JWTMiddleware → RateLimitMiddleware → Router
```

- **JWTMiddleware**：全局中间件，解析 Token → 检查黑名单 → 检查封禁 → 注入 `request.state.user_id`
- **RateLimitMiddleware**：限流 120次/60秒（GET/OPTIONS 豁免），Redis 不可用时跳过
- **get_current_user**：路由级依赖项，从 `request.state` 提取 `user_id`

### 关键架构决策 (ADR)

- **[ADR-001] 全链路异步**：所有 I/O 使用 async/await，禁止同步阻塞调用。
- **[ADR-002] 本地优先运行**：不依赖 Docker/虚拟机，PostgreSQL 用 brew 安装，Redis 可选。原因：开发环境轻量化，零外部依赖启动。
- **[ADR-003] Redis 降级**：`_InMemoryRedis` 实现相同接口，连不上 Redis 自动切换。原因：本地开发不需要额外服务。
- **[ADR-004] 数据库 ID**：所有主键使用 UUID 字符串（36 字符）。原因：避免暴露业务量级。
- **[ADR-005] 统一响应格式**：所有 API 返回 `BaseResponse`，异常通过全局处理器转换。原因：前端统一处理。
- **[ADR-006] 测试数据库**：SQLite 内存数据库，通过 `dependency_overrides[get_db]` 覆盖。
- **[ADR-007] 软删除**：房源使用 `is_active=False` 软删除，其他实体暂用硬删除。
- **[ADR-008] JWT 中间件认证**：全局中间件解析 Token 注入 `request.state`，路由通过 `Depends(get_current_user)` 取值。原因：集中认证逻辑，支持 Token 黑名单和用户封禁。

### 禁止事项

- ❌ 在业务代码中使用 `print()`，必须使用 Python 标准 `logging` 模块
- ❌ 在 Router 中直接写 SQL 查询，必须通过 Service
- ❌ 使用 `HTTPException`，必须使用 `AppException` 子类（`NotFoundException` 等）
- ❌ 硬编码字符串常量，必须定义为常量变量
- ❌ 在路由函数中写超过 20 行的逻辑，必须下沉到 Service 层
- ❌ 在异步函数中使用同步 HTTP 客户端
- ❌ 在测试中使用真实 PostgreSQL
- ❌ 禁止 `SELECT *`，只查询需要的字段
- ❌ 禁止 N+1 查询，列表查询必须使用 `selectinload` 预加载关联数据

---

## 6. 编码规范

### 6.1 命名规范

| 类型 | 风格 | 示例 |
|---|---|---|
| 变量/函数 | snake_case | `user_name`, `get_booking()` |
| 类 | PascalCase | `BookingCreate`, `NotFoundException` |
| 常量 | UPPER_SNAKE | `PLATFORM_FEE_RATE`, `DEFAULT_PAGE_SIZE` |
| 私有函数 | 前缀 `_` | `_get_payment()`, `_require_admin()` |
| 布尔字段 | is_/has_ 前缀 | `is_active`, `is_read`, `is_primary` |
| 数据库表名 | snake_case, 复数 | `users`, `bookings`, `audit_logs` |
| 路由文件名 | 复数名词 | `bookings.py`, `admin.py` |
| Service 文件名 | 单数名词 | `booking.py`（对应 `bookings.py`） |

### 6.2 错误处理

```python
# ✅ 正确：使用自定义异常
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException

if not listing or not listing.is_active:
    raise NotFoundException("房源不存在或不可预订")

if booking.status != "pending":
    raise BadRequestException("订单状态不允许支付")

if user_id not in (booking.guest_id, booking.host_id):
    raise ForbiddenException()

# ❌ 错误：直接使用 HTTPException
raise HTTPException(status_code=404, detail="Not found")  # 不要这样用
```

### 6.3 Service 层模式

```python
# ✅ 标准 Service 函数签名
async def create_booking(db: AsyncSession, guest_id: str, data: BookingCreate) -> Booking:
    if data.check_in >= data.check_out:
        raise BadRequestException("入住日期必须早于退房日期")

    listing = await db.get(Listing, data.listing_id)
    if not listing or not listing.is_active:
        raise NotFoundException("房源不存在")

    nights = (data.check_out - data.check_in).days
    total_price = Decimal(str(listing.price_per_night)) * Decimal(nights)

    booking = Booking(listing_id=data.listing_id, guest_id=guest_id, ...)
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
```

### 6.4 Schema 模式

```python
# ✅ 请求 Schema：使用 Field 做字段级校验
class ListingCreate(BaseModel):
    title: str = Field(..., max_length=200)
    price_per_night: Decimal = Field(..., gt=0)
    max_guests: int = Field(default=1, ge=1)

# ✅ 响应 Schema：启用 from_attributes
class BookingResponse(BaseModel):
    id: str
    status: str
    total_price: float
    created_at: datetime
    model_config = {"from_attributes": True}

# ✅ 统一响应包装
from app.schemas.common import BaseResponse

class BookingListResponse(BaseResponse[list[BookingResponse]]):
    pass
```

### 6.5 查询模式

```python
# ✅ 列表查询：selectinload 预加载 + 分页
result = await db.execute(
    select(Listing)
    .where(Listing.status == "approved", Listing.is_active.is_(True))
    .options(selectinload(Listing.photos))
    .offset((page - 1) * size).limit(size)
)
return list(result.scalars().all())

# ✅ 批量更新
await db.execute(update(Listing).where(Listing.id == lid).values(status="approved"))

# ❌ 禁止 N+1
for booking in bookings:
    listing = await db.get(Listing, booking.listing_id)
```

### 6.6 类型注解

```python
# ✅ 完整类型注解
async def get_user_bookings(db: AsyncSession, user_id: str, role: str = "guest") -> list[Booking]:
    ...

# ✅ 可空类型
avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
```

### 6.7 安全规范

- 用户输入必须通过 Pydantic Schema 校验（`Field` 约束）
- SQL 查询必须使用 SQLAlchemy ORM，禁止字符串拼接
- JWT Token：access_token 30 分钟过期，refresh_token 7 天过期
- 密码使用 bcrypt 哈希存储
- 敏感信息不得出现在日志或错误响应中
- 认证通过全局 `JWTMiddleware` + 路由级 `Depends(get_current_user)`
- CORS 通过 `CORS_ORIGINS` 环境变量配置，默认 `http://localhost:3001`
- 文件上传限制：`.jpg/.jpeg/.png/.gif/.webp`，大小 ≤ `MAX_UPLOAD_SIZE_MB` MB

---

## 7. 测试策略

### 测试金字塔

```
        /  E2E  \           <- 5%   核心用户流程（暂未实现）
       / 集成测试 \          <- 25%  API 端点 + 数据库
      /  单元测试   \        <- 70%  Service 层业务逻辑
```

### 当前测试覆盖

| 测试文件 | 覆盖模块 | 测试数量 | 测试内容 |
|---|---|---|---|
| `test_root.py` | 根路由 | 1 | 健康检查 |
| `test_auth.py` | 认证 | 3 | 注册/登录/Token刷新 |
| `test_listings.py` | 房源 | 7 | 创建/搜索/详情/审核/照片 |
| `test_bookings.py` | 预订 | 4 | 创建/支付/取消/列表 |
| **总计** | | **15** | |

### 测试基础设施

```python
# backend/tests/conftest.py
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 每个测试自动创建/销毁表
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 覆盖数据库依赖
app.dependency_overrides[get_db] = override_get_db

# 异步 HTTP 测试客户端
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

### 测试规范

```python
# 命名：test_<被测函数>_<场景>_<期望结果>
# 结构：Arrange -> Act -> Assert

@pytest.mark.asyncio
async def test_create_booking_with_valid_data_returns_booking(client: AsyncClient):
    # Arrange
    reg = await client.post("/api/auth/register", json={
        "username": "guest1", "email": "guest1@test.com", "password": "Test1234!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post("/api/listings/", json={
        "title": "房源A", "city": "北京", "price_per_night": 100, "max_guests": 2
    }, headers=headers)
    lid = listing.json()["id"]
    await client.post(f"/api/listings/{lid}/approve", json={"action": "approve"})

    # Act
    resp = await client.post("/api/bookings/", json={
        "listing_id": lid, "check_in": "2026-07-01", "check_out": "2026-07-03", "guests": 1
    }, headers=headers)

    # Assert
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"
```

### Mock 策略

- ✅ SQLite 内存数据库替代 PostgreSQL
- ✅ `dependency_overrides` 覆盖数据库依赖
- ✅ Redis 内存降级，测试中自动生效
- ❌ 不 Mock 内部 Service 调用
- ❌ 不 Mock 数据库查询

---

## 8. 数据库规范

### 模型基类

```python
class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

# 所有模型继承方式：
class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
```

### 主键规范

- 所有主键：UUID 字符串（36 字符），`String(36)`
- 默认值：`default=lambda: str(uuid.uuid4())`

### 索引规范

| 字段 | 原因 |
|---|---|
| `User.email` | 登录查询 |
| `User.username` | 用户名唯一查询 |
| `Listing.city` | 按城市搜索 |
| `Listing.host_id` | 房东的房源列表 |
| `Booking.listing_id` | 房源的预订列表 |
| `Booking.guest_id` / `host_id` | 用户预订列表 |
| `Payment.booking_id` | 预订的支付记录 |
| `Message.conversation_id` | 会话的消息列表 |
| `Note.user_id` | 用户的笔记列表 |
| `Review.listing_id` | 房源的评价列表 |

### 迁移规范

```bash
alembic revision --autogenerate -m "描述"   # 生成迁移
alembic upgrade head                         # 执行迁移
alembic downgrade -1                         # 回滚
alembic current                              # 当前版本
```

- 每次 schema 变更必须生成迁移文件
- 大表加 NOT NULL 列必须提供 `server_default`

---

## 9. API 规范

### 统一前缀

所有业务 API 以 `/api` 开头。

### 完整端点列表

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/health` | 否 | 健康检查（DB + Redis 状态） |
| POST | `/api/auth/register` | 否 | 注册新用户 |
| POST | `/api/auth/login` | 否 | 登录 |
| POST | `/api/auth/refresh` | 否 | 刷新 Token |
| GET | `/api/users/me` | 是 | 当前用户资料 |
| GET | `/api/listings/search` | 否 | 搜索房源（城市/价格/人数/分页） |
| GET | `/api/listings/{id}` | 否 | 房源详情 + 照片 |
| POST | `/api/listings/` | 是 | 创建房源（status=pending） |
| PUT | `/api/listings/{id}` | 是 | 更新房源（仅房东） |
| DELETE | `/api/listings/{id}` | 是 | 删除房源（软删除） |
| POST | `/api/listings/{id}/approve` | 是 | 审核房源（仅管理员） |
| GET | `/api/listings/{id}/photos` | 否 | 房源照片列表 |
| POST | `/api/listings/{id}/photos` | 是 | 添加照片 |
| DELETE | `/api/listings/{id}/photos/{photo_id}` | 是 | 删除照片 |
| POST | `/api/bookings/` | 是 | 创建预订 |
| GET | `/api/bookings/` | 是 | 我的预订列表（role=guest/host） |
| POST | `/api/bookings/{id}/pay` | 是 | 支付（10% 平台费） |
| POST | `/api/bookings/{id}/cancel` | 是 | 取消/退款 |
| POST | `/api/messages/send` | 是 | 发送消息 |
| GET | `/api/messages/conversations` | 是 | 会话列表 |
| GET | `/api/messages/conversations/{id}/messages` | 是 | 消息列表 |
| POST | `/api/messages/conversations/{id}/read` | 是 | 标记已读 |
| GET | `/api/social/notes` | 否 | 笔记列表 |
| POST | `/api/social/notes` | 是 | 创建笔记 |
| POST | `/api/social/notes/{id}/like` | 是 | 点赞 |
| POST | `/api/social/notes/{id}/unlike` | 是 | 取消点赞 |
| POST | `/api/social/notes/{id}/comments` | 是 | 评论 |
| POST | `/api/social/follow/{id}` | 是 | 关注用户 |
| POST | `/api/social/unfollow/{id}` | 是 | 取消关注 |
| POST | `/api/reviews/` | 是 | 创建评价（1-5分） |
| GET | `/api/reviews/listing/{id}` | 否 | 房源评价列表 |
| POST | `/api/upload` | 是 | 文件上传（图片） |
| GET | `/api/admin/stats` | 是(管理员) | 平台统计数据 |
| POST | `/api/ai/chat` | 是 | AI 聊天 |

### HTTP 状态码使用

| 状态码 | 场景 | 示例 |
|---|---|---|
| 200 | 成功读取/更新 | GET 列表、POST 支付/取消 |
| 201 | 成功创建 | POST 注册、创建预订 |
| 204 | 成功删除 | DELETE 房源、删除照片 |
| 400 | 请求参数错误 | `BadRequestException` |
| 401 | 未认证 | `UnauthorizedException` / Token 无效 |
| 403 | 无权限 | `ForbiddenException` / 非房东 / 用户被封禁 |
| 404 | 资源不存在 | `NotFoundException` |
| 409 | 资源冲突 | `ConflictException` / 邮箱已注册 |
| 422 | 参数校验失败 | Pydantic 自动校验 |
| 429 | 请求过于频繁 | RateLimitMiddleware |

### 认证方式

```bash
# 请求头（可选，公开接口不需要）
Authorization: Bearer <access_token>

# JWT 结构（HS256）
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "jti": "token-unique-id",   # 用于黑名单检查
  "type": "access",
  "role": "user"              # user/host/admin
}
```

### 路由函数模式

```python
# ✅ 标准路由（需要认证）
@router.post("/", response_model=BaseResponse[BookingResponse], status_code=201)
async def create(
    data: BookingCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await create_booking(db, user_id, data)
    return BaseResponse(success=True, data=BookingResponse.model_validate(booking))

# ✅ 公开路由（不需要认证）
@router.get("/search", response_model=BaseResponse[list[ListingResponse]])
async def search(
    city: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    listings = await search_listings(db, city)
    return BaseResponse(success=True, data=listings)

# ✅ 管理员路由（需要 admin 角色检查）
@router.get("/stats", response_model=BaseResponse)
async def get_stats(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, user_id)
    ...
```

---

## 10. Git 工作流

### 分支策略

```
main              ← 生产环境，保护分支
  └── develop     ← 开发主线，CI 必须通过
       ├── feature/xxx   ← 功能分支
       ├── fix/xxx       ← Bug 修复
       └── refactor/xxx  ← 重构
```

### CI 流程 (GitHub Actions)

```
触发: push/PR → develop 或 main
→ Checkout → Python 3.12 → pip install
→ Ruff check backend/
→ Ruff format --check backend/
→ pytest backend/ -q
→ 超时: 15 分钟
```

### 提交规范 (Conventional Commits)

```
feat(auth): add OAuth2 login
fix(booking): prevent double booking
refactor(service): extract payment logic
test(booking): add edge case tests
docs: update API documentation
chore: update dependencies
```

格式：`<type>(<scope>): <description>`
- type: feat / fix / refactor / test / docs / chore / perf / style
- scope: auth / booking / listing / message / social / review / admin / ai / config
- description: 小写开头，祈使句，< 72 字符

---

## 11. 架构审计与重构路线图

> 最后审计日期：2026-05-19
> 重构进度：Phase 0-10 已完成，Phase 11-12 待执行

### 架构完成度

| 维度 | 状态 | 说明 |
|---|---|---|
| 统一响应格式 | ✅ | BaseResponse 全量覆盖 |
| 自定义异常体系 | ✅ | 全部 router/middleware 使用 AppException，HTTPException 已清除 |
| JWT 全局中间件 | ✅ | JWTMiddleware + Token 黑名单 + 封禁检查 |
| Redis 内存降级 | ✅ | _InMemoryRedis 自动切换 |
| 前端 vanilla JS | ✅ | api-client.js + app.js，无第三方依赖 |
| 管理后台 | ✅ | 12 个 admin 端点 + 审计日志 |
| 种子数据 | ✅ | seed.py + POST /api/admin/seed |
| 测试覆盖 | 🟡 | 69 个测试（目标 80%+） |
| 路由无直接 SQL | ✅ | 所有查询下沉到 service 层 |

### 严重问题（必须修复）

| # | 问题 | 影响 | 状态 |
|---|---|---|---|
| 1 | ~~routers/auth.py 仍用 HTTPException~~ | ~~错误响应格式不统一~~ | ✅ 已修复 |
| 2 | ~~routers/users.py 路由里直接写 select(User)~~ | ~~违反"路由不写 SQL"架构规则~~ | ✅ 已修复 |
| 3 | ~~routers/listings.py 审核端点无管理员权限检查~~ | ~~任何登录用户都能审核房源~~ | ✅ 已修复 |
| 4 | **测试仅 69 个**（目标 80%+ 覆盖率） | 覆盖率不足 | 🟡 部分完成 |
| 5 | **Notification 模型已定义但无 router/service** | 死代码 | ⬜ 待处理 |
| 6 | ~~评价条件写错：confirmed 应为 completed~~ | ~~未退房就能评价~~ | ✅ 已修复 |

### 中等问题

| # | 问题 | 状态 |
|---|---|---|
| 7 | `.env` 的 `CORS_ORIGINS` 含 `http://localhost:8000`，后端已是 8001 | ⬜ 待处理 |
| 8 | `pyproject.toml` 依赖 `aiokafka`/`arq`/`elasticsearch`/`jinja2`/`aiofiles`，实际未使用 | ⬜ 待处理 |
| 9 | `services/social.py` 和 `services/review.py` 返回 dict 而非 ORM 对象 | ⬜ 待处理 |
| 10 | ~~admin.py 顶部 `import sys as _sys` 和 `from pathlib import Path as _Path` 命名不规范~~ | ✅ 已修复 |
| 11 | ~~WebSocket 端点 `/api/messages/ws` 未加入 `EXEMPT_PATHS`~~ | ✅ 已修复 |
| 12 | `User.is_active` 同时用于"封禁"和"软删除"，语义不清晰 | ⬜ 待处理 |
| 13 | `Booking.status` 修改无事务保护 | ⬜ 待处理 |

### 低优先级

| # | 问题 |
|---|---|
| 14 | `tasks/` 目录为空，ARQ 异步任务未实现 |
| 15 | Elasticsearch 未实际集成 |
| 16 | 日志未结构化，缺少 request_id |
| 17 | seed.py 硬编码 DB_URL |

### 重构路线图

```
Phase 0-7  ✅ 已完成（安全修复/核心功能/测试/运维/前端/增强/种子数据）
Phase 8    ✅ 基础设施框架 — exceptions/common/handlers/api-client
Phase 9    ✅ 认证体系 — JWTMiddleware 重写/Token黑名单/logout/密码重置
Phase 10   ✅ 统一响应 — 11个router返回BaseResponse/10个service用自定义异常/路由无直接SQL
Phase 11   ⬜ 模型扩展 — AuditLog+Notification/User新字段/Alembic迁移/Admin补全
Phase 12   ⬜ 测试体系 — 角色fixtures/适配BaseResponse/新增测试/覆盖率≥80%
Phase 13   ✅ 前端完善（已完成）
Phase 14   ✅ Docker移除 & 本地化（已完成）
```

### 可移除的依赖

```toml
# pyproject.toml 中以下依赖实际未使用，可安全移除：
"aiokafka>=0.12.0"         # Kafka 已移除
"arq>=0.26.0"              # tasks/ 目录为空
"elasticsearch[async]>=8.17.0"  # elasticsearch_enabled=false
"jinja2>=3.1.0"            # 无模板渲染
"aiofiles>=24.1.0"         # 未发现使用
```

---

## 12. 环境变量

| 变量名 | 用途 | 必填 | 默认值 |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL 连接串 | ✅ | — |
| `JWT_SECRET_KEY` | JWT 签名密钥 | ✅ | — |
| `REDIS_URL` | Redis 连接串（可选） | ❌ | `redis://localhost:6379/0` |
| `JWT_ALGORITHM` | JWT 算法 | ❌ | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | access_token 过期(分) | ❌ | `30` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | refresh_token 过期(天) | ❌ | `7` |
| `CORS_ORIGINS` | CORS 允许来源（逗号分隔） | ❌ | `http://localhost:3001` |
| `ELASTICSEARCH_HOSTS` | ES 地址 | ❌ | `["http://localhost:9200"]` |
| `ELASTICSEARCH_ENABLED` | 是否启用 ES | ❌ | `false` |
| `DEEPSEEK_API_KEY` | DeepSeek AI 密钥 | ❌ | `""` |
| `AI_ENABLED` | 是否启用 AI | ❌ | `false` |
| `SENTRY_DSN` | Sentry 错误追踪 | ❌ | `""` |
| `UPLOAD_DIR` | 文件上传目录 | ❌ | `uploads` |
| `MAX_UPLOAD_SIZE_MB` | 最大上传大小(MB) | ❌ | `10` |
| `DEBUG` | 调试模式 | ❌ | `false` |
| `LOGIN_RATE_LIMIT` | 登录限流次数 | ❌ | `10` |
| `LOGIN_RATE_WINDOW` | 登录限流窗口(秒) | ❌ | `300` |

---

## 13. 常用命令速查

```bash
# 一键启动（推荐）
./run.sh                          # 前后端同时启动

# 开发
make dev                          # 启动后端 (uvicorn --reload --port 8001)
make test                         # 运行全部测试
make lint                         # Ruff lint
make format                       # Ruff 自动格式化
make precommit                    # format + lint + test
make seed                         # 生成测试数据
make clean                        # 清理缓存

# 数据库
brew services start postgresql@14 # 启动 PostgreSQL
createdb stayhub                  # 创建数据库
alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic downgrade -1

# 生成测试数据
PYTHONPATH=backend python backend/scripts/seed.py

# 前端（纯静态，无需构建）
python3 -m http.server 3001 -d frontend/
```

---

## 14. 给 Claude 的特殊指令

### 代码生成规则

1. **新功能必须包含四件套**：Router + Service + Schema + Test
2. **先写测试，再写实现**（TDD 优先）
3. **遵循现有代码风格**：模仿 `booking.py` / `listing.py` 的模式
4. **路由函数保持薄**：只做参数接收 + 调用 Service + 包装 `BaseResponse` 返回
5. **错误使用自定义异常**：`NotFoundException` / `BadRequestException` / `ForbiddenException`，不要用 `HTTPException`
6. **响应包装 BaseResponse**：`return BaseResponse(success=True, data=...)`
7. **Schema 必须配置** `model_config = {"from_attributes": True}`
8. **新增模型必须注册到** `models/__init__.py` 的 `__all__` 列表
9. **生成的代码必须通过**：`ruff check` + `ruff format` + `pytest`
10. **不得引入新的第三方依赖**而不先征询开发者同意

### 项目特有约定

- 所有 ID 字段类型为 `str`（UUID 字符串），不是 `int`
- 价格字段类型为 `Decimal`（Numeric(10, 2)），Schema 中用 `float` 序列化
- 时间字段使用 `DateTime(timezone=True)`
- 状态字段使用 `String(20)`，值为英文小写（pending/confirmed/cancelled/approved/rejected）
- 认证用户通过 `user_id: str = Depends(get_current_user)` 获取
- 测试中注册用户默认密码为 `"Test1234!"`
- 房源创建后 status 为 `pending`，需管理员通过 `/approve` 审核
- Redis 操作统一通过 `get_redis()` 获取客户端，可能返回内存实现
- 前端路由豁免认证：`EXEMPT_PATHS` 集合定义在 `middleware/auth.py`

### 沟通偏好

- 语言：中文（代码注释和 Git 提交信息用英文）
- 解释详细程度：适中 — 关键决策需要解释原因
- 遇到不确定时：先提出方案和理由，让我确认后再实现
- 代码风格：双引号、行宽 100 字符、import 使用 Ruff 自动排序
