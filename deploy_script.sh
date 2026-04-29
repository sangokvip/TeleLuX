#!/bin/bash
# TeleLuX VPS完整部署脚本

set -e  # 遇到错误立即退出

echo "🚀 开始部署TeleLuX到VPS..."

# 检查Python版本
python3_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python3_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本过低，需要3.8+，当前版本: $python3_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python3_version"

# 创建项目目录
PROJECT_DIR="$HOME/TeleLuX"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "📁 创建项目文件..."

# 创建requirements.txt
cat > requirements.txt << 'EOF'
python-telegram-bot==20.7
tweepy==4.14.0
python-dotenv==1.0.0
aiohttp==3.9.5
EOF

# 创建.env文件模板
cat > .env << 'EOF'
# Twitter/X RapidAPI 配置
RAPIDAPI_KEY=your_rapidapi_key_here

# Telegram 配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
ADMIN_CHAT_ID=your_admin_chat_id_here
ADMIN_USER_IDS=your_admin_user_id_here

# 监控配置
TWITTER_USERNAME=xiuchiluchu910
CHECK_INTERVAL=28800
ALLOWED_USERNAMES=mteacherlu,bryansuperb
EOF

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建systemd服务文件
echo "⚙️ 创建系统服务..."
SERVICE_FILE="/etc/systemd/system/telex.service"
USERNAME=$(whoami)

sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=TeleLuX Twitter Monitor
After=network.target

[Service]
Type=simple
User=$USERNAME
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
sudo systemctl daemon-reload

echo "✅ 部署完成！"
echo ""
echo "📝 下一步操作："
echo "1. 编辑配置文件: nano $PROJECT_DIR/.env"
echo "2. 填入你的API密钥和配置"
echo "3. 启动服务: sudo systemctl start telex.service"
echo "4. 启用开机自启: sudo systemctl enable telex.service"
echo "5. 查看状态: sudo systemctl status telex.service"
echo "6. 查看日志: sudo journalctl -u telex.service -f"
echo ""
echo "🎉 TeleLuX已准备就绪！"
