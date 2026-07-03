#!/bin/bash
set -e

# ============================================================
# AI Trading API 部署脚本
# 适用于 Ubuntu 系统
# ============================================================

PROJECT_DIR="/home/ubuntu/projects/ai-trading"
GIT_URL="https://github.com/horgrix/ai-trading.git"
NGINX_CONF="/etc/nginx/conf.d/api.horgrix.com.conf"
API_SERVICE_NAME="ai-trading-api"
API_SERVICE_FILE="/etc/systemd/system/${API_SERVICE_NAME}.service"
TASK_SERVICE_NAME="ai-trading-crawler"
TASK_SERVICE_FILE="/etc/systemd/system/${TASK_SERVICE_NAME}.service"

echo "========================================"
echo "  AI Trading 部署脚本"
echo "========================================"

# ==================== 1. 从 Git 仓库获取代码 ====================

echo ""
echo "[1/6] 获取代码..."

if [ -d "$PROJECT_DIR/.git" ]; then
    echo "  代码库已存在，执行 git pull..."
    cd "$PROJECT_DIR"
    git pull origin master
else
    echo "  克隆代码库..."
    mkdir -p "$(dirname "$PROJECT_DIR")"
    git clone "$GIT_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# ==================== 2. 创建虚拟环境并安装依赖 ====================

echo ""
echo "[3/6] 创建虚拟环境并安装依赖..."

cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  虚拟环境已创建。"
else
    echo "  虚拟环境已存在，跳过创建。"
fi

.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -e . -q
echo "  依赖安装完成。"

# ==================== 3. 创建 systemd 服务 ====================
# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

sudo tee "$API_SERVICE_FILE" > /dev/null << SERVICEEOF
[Unit]
Description=ai-trading-api
After=network.target mysql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/.venv/bin/python3 ${PROJECT_DIR}/src/ai-trading-api/main.py
Restart=always
RestartSec=10
StandardOutput=append:${PROJECT_DIR}/logs/ai-trading-api.log
StandardError=append:${PROJECT_DIR}/logs/ai-trading-api_error.log

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "  服务文件已创建: $API_SERVICE_FILE"

sudo tee "$TASK_SERVICE_FILE" > /dev/null << SERVICEEOF
[Unit]
Description=ai-trading-crawler
After=network.target mysql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/.venv/bin/python3 ${PROJECT_DIR}/src/ai-trading-crawler/main.py
Restart=always
RestartSec=10
StandardOutput=append:${PROJECT_DIR}/logs/ai-trading-crawler.log
StandardError=append:${PROJECT_DIR}/logs/ai-trading-crawler_error.log

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "  服务文件已创建: $TASK_SERVICE_FILE"

# ==================== 4. 配置 NGINX ====================

# 要检查的配置块
CHECK_PATTERN="location /api/v2/market/"

# 要添加的配置内容
NEW_LOCATION_CONFIG='
    location /api/v2/market/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

    }'

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否已存在配置
if grep -q "$CHECK_PATTERN" "$NGINX_CONF"; then
    echo -e "${GREEN}✓ 配置已存在: $CHECK_PATTERN${NC}"
    echo "无需添加新配置。"
else
    echo -e "${YELLOW}未找到配置: $CHECK_PATTERN${NC}"
    echo "正在添加配置..."

        # 创建备份
    BACKUP_FILE="${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$NGINX_CONF" "$BACKUP_FILE"
    echo -e "${GREEN}已创建备份: $BACKUP_FILE${NC}"
    
    # 查找最后一个 location 块的结束位置并插入新配置
    # 在最后一个 } 之前插入（在第一个 server 块内）
    # 更精确的方式：在 /api/v2/financial/ 的 location 块之后插入
    
    # 使用 awk 或 sed 在指定位置插入配置
    # 方法：在包含 "location /api/v2/financial/" 的块结束后插入
    
    # 创建一个临时文件
    TEMP_FILE=$(mktemp)
    
    # 使用 awk 处理配置文件
    awk -v new_config="$NEW_LOCATION_CONFIG" '
    /location \/api\/v2\/financial\// {
        print $0
        in_financial_block = 1
        brace_count = 0
        next
    }
    in_financial_block {
        print $0
        # 计算大括号
        for (i = 1; i <= length($0); i++) {
            char = substr($0, i, 1)
            if (char == "{") brace_count++
            if (char == "}") brace_count--
        }
        # 当大括号匹配完成（回到0），表示块结束
        if (brace_count == 0) {
            in_financial_block = 0
            # 在块结束后插入新配置
            print new_config
        }
        next
    }
    { print $0 }
    ' "$NGINX_CONF" > "$TEMP_FILE"
    
    # 替换原文件
    mv "$TEMP_FILE" "$NGINX_CONF"
    
    echo -e "${GREEN}✓ 配置已成功添加${NC}"

        # 测试 nginx 配置
    echo "正在测试 Nginx 配置..."
    if sudo nginx -t 2>/dev/null; then
        echo -e "${GREEN}✓ Nginx 配置测试通过${NC}"
        
        # 重载 nginx
        echo "正在重载 Nginx..."
        if sudo nginx -s reload 2>/dev/null || sudo systemctl reload nginx 2>/dev/null; then
            echo -e "${GREEN}✓ Nginx 已成功重载${NC}"
        else
            echo -e "${RED}✗ Nginx 重载失败，请手动检查${NC}"
            echo "可以使用备份文件恢复: $BACKUP_FILE"
            exit 1
        fi
    else
        echo -e "${RED}✗ Nginx 配置测试失败，正在恢复备份...${NC}"
        cp "$BACKUP_FILE" "$NGINX_CONF"
        echo -e "${YELLOW}已恢复到备份文件: $BACKUP_FILE${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}操作完成！${NC}"

# ==================== 5. 重载并启动服务 ====================

echo ""
echo "[6/6] 启动服务..."

sudo systemctl daemon-reload
sudo systemctl enable "$API_SERVICE_NAME"
sudo systemctl restart "$API_SERVICE_NAME"
sudo systemctl enable "$TASK_SERVICE_NAME"
sudo systemctl restart "$TASK_SERVICE_NAME"

echo "  服务已启动。"

# ==================== 验证部署 ====================

echo ""
echo "========================================"
echo "  验证部署..."
echo "========================================"

sleep 2

HEALTH_RESPONSE=$(curl -s --connect-timeout 5 http://127.0.0.1/api/v2/market/health 2>/dev/null || echo "")

if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    echo ""
    echo "  ✓ 部署成功！"
    echo "  健康检查响应: $HEALTH_RESPONSE"
else
    echo ""
    echo "  ✗ 健康检查失败，请检查日志："
    echo "    journalctl -u ${API_SERVICE_NAME} -n 50 --no-pager"
    echo "    或: tail -f ${PROJECT_DIR}/logs/ai-trading-api.log"
    exit 1
fi