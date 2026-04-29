#!/bin/bash
# TeleLuX 一键部署脚本 - 包含所有项目文件

set -e

echo "🚀 TeleLuX 一键部署脚本"
echo "=========================="

# 检查Python版本
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python3"
    exit 1
fi

python3_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python3_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本过低，需要3.8+，当前版本: $python3_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python3_version"

# 创建项目目录
PROJECT_DIR="$HOME/TeleLuX"
echo "📁 创建项目目录: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# 创建requirements.txt
echo "📦 创建依赖文件..."
cat > requirements.txt << 'EOF'
python-telegram-bot==20.7
tweepy==4.14.0
python-dotenv==1.0.0
aiohttp==3.9.5
EOF

# 创建config.py
echo "⚙️ 创建配置模块..."
cat > config.py << 'EOF'
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # Twitter/X RapidAPI配置
    RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    
    # Telegram配置
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
    ADMIN_USER_IDS = [int(x.strip()) for x in os.getenv('ADMIN_USER_IDS', ADMIN_CHAT_ID or '').split(',') if x.strip().isdigit()]
    
    # 监控配置
    TWITTER_USERNAME = os.getenv('TWITTER_USERNAME', 'xiuchiluchu910')
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '3000'))
    
    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'tweets.db')
    
    @classmethod
    def validate(cls):
        """验证必需的配置项"""
        required_configs = [
            ('RAPIDAPI_KEY', cls.RAPIDAPI_KEY),
            ('TELEGRAM_BOT_TOKEN', cls.TELEGRAM_BOT_TOKEN),
            ('TELEGRAM_CHAT_ID', cls.TELEGRAM_CHAT_ID),
        ]
        
        missing_configs = []
        for name, value in required_configs:
            if not value:
                missing_configs.append(name)
        
        if missing_configs:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing_configs)}")
        
        return True
EOF

# 创建.env文件模板
echo "🔧 创建环境变量模板..."
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

# 数据库配置
DATABASE_PATH=tweets.db
EOF

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📥 安装Python依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ 基础环境部署完成！"
echo ""
echo "📝 接下来需要手动操作："
echo "1. 编辑配置文件: nano $PROJECT_DIR/.env"
echo "2. 填入你的API密钥和配置信息"
echo "3. 上传其他项目文件（main.py, database.py, twitter_monitor.py, telegram_bot.py）"
echo "4. 测试运行: source venv/bin/activate && python main.py"
echo ""
echo "🔗 完整部署指南请查看: VPS_DEPLOY_GUIDE.md"
echo ""

# 询问是否创建系统服务
read -p "是否现在创建系统服务？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
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
    
    sudo systemctl daemon-reload
    echo "✅ 系统服务创建完成！"
    echo ""
    echo "🎯 服务管理命令："
    echo "启动服务: sudo systemctl start telex.service"
    echo "停止服务: sudo systemctl stop telex.service"
    echo "查看状态: sudo systemctl status telex.service"
    echo "查看日志: sudo journalctl -u telex.service -f"
    echo "开机自启: sudo systemctl enable telex.service"
fi

echo ""
echo "🎉 TeleLuX部署脚本执行完成！"
echo "项目目录: $PROJECT_DIR"
