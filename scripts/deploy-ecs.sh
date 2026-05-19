#!/bin/bash
set -euo pipefail

echo "=== LiveHappy ECS 部署脚本 ==="

APP_DIR="/opt/livehappy"
BRANCH="main"

if [ ! -f "$APP_DIR/.env" ]; then
  echo "错误: $APP_DIR/.env 不存在"
  exit 1
fi

source "$APP_DIR/.env"

if [ -d "$APP_DIR" ]; then
  cd "$APP_DIR" && git pull origin "$BRANCH"
else
  git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "--- 安装 Python 依赖 ---"
cd "$APP_DIR/backend"
pip3 install -e ".[dev]" --quiet

echo "--- 执行数据库迁移 ---"
alembic upgrade head

echo "--- 重启后端 ---"
systemctl daemon-reload
systemctl restart livehappy

echo "--- 重建前端 ---"
if [ -d "$APP_DIR/frontend/public" ]; then
  cp -r "$APP_DIR/frontend/public" /usr/share/nginx/livehappy/
fi

echo "--- 健康检查 ---"
sleep 3
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo "健康检查通过"
else
  echo "警告: 健康检查失败，请手动检查"
fi

echo "=== 部署完成 ==="
