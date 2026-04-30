#!/bin/bash
# TeleLuX VPS更新脚本

echo "🔄 开始更新TeleLuX系统..."

# 检查项目目录
PROJECT_DIR="$HOME/TeleLuX"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    echo "请先运行部署脚本"
    exit 1
fi

cd "$PROJECT_DIR"

echo "⏹️  停止服务..."
sudo systemctl stop telex.service

echo "📥 更新代码..."
if [ -d ".git" ]; then
    # 强制同步远程代码，丢弃所有本地修改（.env 已在 .gitignore 中，不受影响）
    git fetch origin main
    git reset --hard origin/main
else
    echo "⚠️  不是Git仓库，请手动上传新文件"
    echo "或者重新克隆仓库"
fi

echo "🧹 清理Python缓存..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

echo "🐍 激活虚拟环境..."
source venv/bin/activate

echo "📦 更新依赖..."
pip install -r requirements.txt --upgrade

echo "🚀 重启服务..."
sudo systemctl start telex.service

echo "📊 检查服务状态..."
sleep 3
sudo systemctl status telex.service --no-pager

echo "✅ 更新完成！"
echo ""
echo "📋 查看日志: sudo journalctl -u telex.service -f"
echo "📊 查看状态: sudo systemctl status telex.service"
