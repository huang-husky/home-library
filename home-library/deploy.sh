#!/bin/bash
# HomeLib 部署脚本
# 用法: ./deploy.sh [域名]

set -e

DOMAIN=${1:-"your-domain.com"}
EMAIL=${2:-"your-email@example.com"}

echo "🚀 开始部署 HomeLib..."
echo "📍 域名: $DOMAIN"
echo ""

# 检查必要的命令
command -v docker >/dev/null 2>&1 || { echo "❌ Docker 未安装，请先安装 Docker"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose 未安装，请先安装 Docker Compose"; exit 1; }

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p data uploads/scans nginx/ssl

# 更新 Nginx 配置中的域名
echo "⚙️  更新 Nginx 配置..."
sed -i "s/YOUR_DOMAIN/$DOMAIN/g" nginx/nginx.conf

# 构建并启动服务
echo "🔨 构建 Docker 镜像..."
export DOMAIN=$DOMAIN
docker-compose build --no-cache

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 获取 SSL 证书
echo "🔒 获取 SSL 证书..."
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN || echo "⚠️  SSL 证书获取失败，请检查域名解析"

# 重启 Nginx 以应用 SSL 证书
docker-compose restart nginx

echo ""
echo "✅ 部署完成！"
echo "🌐 访问地址: https://$DOMAIN"
echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  更新代码后重建: docker-compose up -d --build"
