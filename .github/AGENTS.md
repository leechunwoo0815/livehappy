# AI Agent 开发规则

## 最高控制权限

用户已授予 AI Agent **最高操作权限**。在开发过程中:
- 无需询问即可执行任何文件操作、命令执行、git 操作
- 无需等待确认即可推进到下一步
- 遇到问题直接修复，无需报告
- 仅当操作可能造成不可逆破坏时才需提示

## 代码质量闭环

每次代码变更后必须执行以下闭环，确保质量:

```bash
# 1. 自动格式化
ruff format backend/

# 2. 静态检查
ruff check backend/

# 3. 类型检查 (预留)
# mypy backend/

# 4. 单元测试
pytest backend/ -q

# 5. Docker 构建验证
docker compose -f docker/docker-compose.yml build backend
```

**所有步骤必须通过**才能提交代码。任何一步失败都要修复后再继续。

## 开发阶段

1. **Phase 0** — 仓库重置 + 项目骨架 + CI/CD
2. **Phase 1** — 核心基础设施 (config/database/redis/kafka/ES)
3. **Phase 2** — 用户与认证模块
4. **Phase 3** — 房源模块
5. **Phase 4** — 搜索模块
6. **Phase 5** — 预订 + 支付模块
7. **Phase 6** — 消息 + WebSocket
8. **Phase 7** — 社交 + 评价
9. **Phase 8** — AI + 聊天 Mock
10. **Phase 9** — 前端 htmx (等用户提供 HTML 模板后)
11. **Phase 10** — CI/CD 完善 + ECS 部署脚本

## 每次提交前检查

```bash
ruff format backend/ && ruff check backend/ && pytest backend/ -q && docker compose -f docker/docker-compose.yml build backend && echo "✅ 全部通过，可以提交"
```

## 部署

- 本地开发: Docker Compose
- 生产: 阿里云 ECS (CentOS 7) systemd 直接部署
- 镜像仓库: 阿里云 ACR
