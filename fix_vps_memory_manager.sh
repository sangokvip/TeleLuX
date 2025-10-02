#!/bin/bash
# VPS修复脚本 - 修复MemoryManager错误

echo "开始修复TeleLuX机器人MemoryManager错误..."

# 备份原始文件
cp /root/TeleLuX/main.py /root/TeleLuX/main.py.backup

echo "正在修复main.py..."

# 修复MemoryManager导入问题
sed -i 's/self.user_activity_manager = utils.MemoryManager(max_size=500, cleanup_threshold=0.8)/from utils import MemoryManager\n        self.user_activity_manager = MemoryManager(max_size=500, cleanup_threshold=0.8)/' /root/TeleLuX/main.py

echo "修复完成！正在验证..."

# 验证修复
if grep -q "from utils import MemoryManager" /root/TeleLuX/main.py; then
    echo "修复成功！"
else
    echo "修复失败，正在恢复备份..."
    cp /root/TeleLuX/main.py.backup /root/TeleLuX/main.py
    exit 1
fi

echo "正在重启服务..."
systemctl restart telex.service

echo "等待服务启动..."
sleep 5

echo "检查服务状态..."
systemctl status telex.service

echo "查看最近的错误日志..."
sudo journalctl -u telex.service -n 20 | grep -E "(ERROR|MemoryManager)"

echo "修复完成！如果还有问题，请查看完整日志。"