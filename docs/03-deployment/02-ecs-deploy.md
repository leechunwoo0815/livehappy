# 阿里云 ECS 部署

## 环境

- CPU: 2 核
- 内存: 2 GB
- 系统: CentOS 7.9
- 域名: saisenyoo.cn

## 安装中间件

```bash
# PostgreSQL
yum install -y postgresql15-server
/usr/pgsql-15/bin/postgresql-15-setup initdb
systemctl enable --now postgresql-15

# Redis
yum install -y redis
systemctl enable --now redis

# Kafka + ZooKeeper (手动安装)
cd /opt
wget https://downloads.apache.org/kafka/3.7.0/kafka_2.13-3.7.0.tgz
tar -xzf kafka_2.13-3.7.0.tgz
```

## 部署后端

```bash
# 安装 Python 3.12
yum install -y python3.12 python3.12-pip

# 拉取代码
git clone https://github.com/leechunwoo0815/livehappy.git /opt/stayhub
cd /opt/stayhub/backend

# 安装依赖
pip3.12 install -e ".[dev]"

# systemd 服务
cat > /etc/systemd/system/stayhub.service << 'EOF'
[Unit]
Description=StayHub Backend
After=network.target postgresql-15.service redis.service

[Service]
Type=simple
WorkingDirectory=/opt/stayhub/backend
ExecStart=/usr/bin/python3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now stayhub
```

## Nginx 反代 + SSL

```bash
yum install -y nginx certbot python3-certbot-nginx

cat > /etc/nginx/conf.d/stayhub.conf << 'EOF'
server {
    listen 80;
    server_name saisenyoo.cn;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name saisenyoo.cn;

    ssl_certificate /etc/letsencrypt/live/saisenyoo.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/saisenyoo.cn/privkey.pem;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /opt/stayhub/frontend/public;
        index index.html;
    }
}
EOF

certbot --nginx -d saisenyoo.cn
systemctl enable --now nginx
```
