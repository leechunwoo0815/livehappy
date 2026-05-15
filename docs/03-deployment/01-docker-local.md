# Docker 本地部署

## 前提

- Docker + Docker Compose 已安装
- 端口 5432/6379/9092/8000/3000 未被占用

## 启动

```bash
# 构建并启动全部服务
docker compose -f docker/docker-compose.yml up -d --build

# 查看状态
docker compose -f docker/docker-compose.yml ps

# 查看日志
docker compose -f docker/docker-compose.yml logs -f
```

## 访问

| 服务 | 地址 |
|---|---|
| 后端 API | http://localhost:8000 |
| 前端 | http://localhost:3000 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Kafka | localhost:9092 |

## 命令

```bash
make dc-up      # 启动
make dc-down    # 停止
make dc-logs    # 日志
make dc-ps      # 状态
```
