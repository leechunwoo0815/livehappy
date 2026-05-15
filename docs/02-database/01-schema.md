# 数据库表结构

## users

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| username | VARCHAR(50) | 用户名, UK |
| email | VARCHAR(255) | 邮箱, UK |
| password_hash | VARCHAR(255) | bcrypt 哈希 |
| avatar | VARCHAR(500) | 头像 URL |
| role | VARCHAR(20) | 角色: user/host/admin |
| bio | TEXT | 个人简介 |
| score | INTEGER | 行为分, 默认 100 |
| last_login | TIMESTAMPTZ | 最后登录 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

## 后续表 (将根据 Phase 逐步添加)

- listings — 房源
- listing_photos — 房源图片
- bookings — 预订
- payments — 支付
- settlements — 分账
- reviews — 评价
- conversations — 会话
- messages — 消息
- notes — 社交笔记
- note_comments — 笔记评论
- note_likes — 笔记点赞
- user_follows — 用户关注
- chat_messages — AI 聊天记录
