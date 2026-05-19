#!/bin/bash
set -euo pipefail

echo "=== LiveHappy 数据库备份 ==="

BACKUP_DIR="/opt/livehappy/backups"
DB_NAME="${POSTGRES_DB:-stayhub}"
DB_USER="${POSTGRES_USER:-stayhub}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "--- 备份数据库 $DB_NAME ---"
pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$FILENAME"

echo "--- 清理 $RETENTION_DAYS 天前的备份 ---"
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "--- 备份文件: $FILENAME ---"
ls -lh "$FILENAME"

echo "=== 备份完成 ==="
