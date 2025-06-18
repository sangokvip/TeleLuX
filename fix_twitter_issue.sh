#!/bin/bash
# Twitter API问题修复脚本

echo "🔧 开始修复Twitter API问题..."

PROJECT_DIR="$HOME/TeleLuX"
cd "$PROJECT_DIR"

echo "1. 停止服务..."
sudo systemctl stop telex.service

echo "2. 运行Twitter API诊断..."
python3 diagnose_twitter.py

echo ""
echo "3. 检查配置文件..."
if [ -f ".env" ]; then
    echo "✅ .env文件存在"
    
    # 检查必要的配置项
    if grep -q "TWITTER_BEARER_TOKEN=" .env; then
        echo "✅ TWITTER_BEARER_TOKEN已配置"
    else
        echo "❌ TWITTER_BEARER_TOKEN未配置"
    fi
    
    if grep -q "TWITTER_USERNAME=" .env; then
        echo "✅ TWITTER_USERNAME已配置"
    else
        echo "❌ TWITTER_USERNAME未配置"
    fi
else
    echo "❌ .env文件不存在"
fi

echo ""
echo "4. 测试网络连接..."
if curl -s --connect-timeout 5 https://api.twitter.com > /dev/null; then
    echo "✅ Twitter API网络连接正常"
else
    echo "❌ Twitter API网络连接失败"
fi

echo ""
echo "5. 检查日志中的错误..."
echo "最近的错误日志:"
sudo journalctl -u telex.service -n 20 | grep -i "error\|fail\|exception" | tail -5

echo ""
echo "6. 重启服务..."
sudo systemctl start telex.service

echo ""
echo "7. 检查服务状态..."
sleep 3
sudo systemctl status telex.service --no-pager

echo ""
echo "✅ 修复脚本执行完成"
echo ""
echo "📋 下一步建议:"
echo "1. 查看诊断结果，确认API配置正确"
echo "2. 如果是速率限制，等待15分钟后重试"
echo "3. 查看实时日志: sudo journalctl -u telex.service -f"
echo "4. 测试功能: 私聊机器人发送'x'"
