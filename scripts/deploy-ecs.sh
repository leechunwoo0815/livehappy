#!/bin/bash
set -euo pipefail

echo "=== StayHub ECS 部署脚本 ==="

# 配置
APP_DIR="/opt/stayhub"
REPO_URL="git@github.com:leechunwoo0815/livehappy.git"
BRANCH="main"

# 拉取代码
if [ -d "$APP_DIR" ]; then
  cd "$APP_DIR" && git pull origin "$BRANCH"
else
  git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
fi

# 安装 Python 依赖
cd "$APP_DIR/backend"
pip3 install -e ".[dev]" --quiet

# 重启后端
systemctl daemon-reload
systemctl restart stayhub

# 重建前端
cp -r "$APP_DIR/frontend/public" /usr/share/nginx/stayhub/

echo "=== 部署完成 ==="
