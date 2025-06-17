# TeleLuX Oracle VPS 部署指南

## 🎯 部署概述

本指南将帮助你将TeleLuX系统完整部署到Oracle VPS上，实现24/7自动运行。

## 📋 准备工作

### 1. VPS要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **内存**: 最少512MB（推荐1GB+）
- **存储**: 最少5GB可用空间
- **网络**: 稳定的互联网连接

### 2. 本地准备
- SSH客户端（Windows可用PuTTY或PowerShell）
- 你的VPS IP地址和登录凭据
- TeleLuX项目文件

## 🚀 部署步骤

### 第一步：连接VPS并准备环境

```bash
# 1. SSH连接到VPS
ssh username@your-vps-ip

# 2. 更新系统包
# Ubuntu/Debian:
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git nano curl -y

# CentOS/RHEL:
sudo yum update -y
sudo yum install python3 python3-pip git nano curl -y

# 3. 验证Python版本（需要3.8+）
python3 --version
```

### 第二步：上传项目文件

#### 方法A：使用自动部署脚本（推荐）

1. **在VPS上下载部署脚本**：
```bash
curl -O https://raw.githubusercontent.com/your-repo/TeleLuX/main/deploy_script.sh
chmod +x deploy_script.sh
./deploy_script.sh
```

2. **手动创建项目文件**：
```bash
# 创建项目目录
mkdir -p ~/TeleLuX
cd ~/TeleLuX

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install python-telegram-bot==20.7 tweepy==4.14.0 python-dotenv==1.0.0 requests==2.31.0 schedule==1.2.0
```

#### 方法B：从本地上传文件

1. **在本地压缩项目**：
```bash
# Windows PowerShell
cd "C:\Users\Administrator\Documents\augment-projects"
Compress-Archive -Path "TeleLuX" -DestinationPath "TeleLuX.zip"

# 上传到VPS
scp TeleLuX.zip username@your-vps-ip:~/
```

2. **在VPS上解压**：
```bash
cd ~
unzip TeleLuX.zip
cd TeleLuX

# 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 第三步：配置环境变量

```bash
# 编辑配置文件
cd ~/TeleLuX
nano .env
```

在`.env`文件中填入你的配置：
```env
# Twitter API 配置
TWITTER_BEARER_TOKEN=你的Twitter_Bearer_Token

# Telegram 配置
TELEGRAM_BOT_TOKEN=你的Telegram_Bot_Token
TELEGRAM_CHAT_ID=你的Telegram_Chat_ID

# 监控配置
TWITTER_USERNAME=xiuchiluchu910
CHECK_INTERVAL=3000
```

### 第四步：测试运行

```bash
# 激活虚拟环境
cd ~/TeleLuX
source venv/bin/activate

# 测试运行
python main.py
```

如果看到启动成功的消息，按`Ctrl+C`停止，继续下一步。

### 第五步：创建系统服务

```bash
# 创建服务文件
sudo nano /etc/systemd/system/telex.service
```

添加以下内容（**替换username为你的实际用户名**）：
```ini
[Unit]
Description=TeleLuX Twitter Monitor
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/TeleLuX
Environment=PATH=/home/username/TeleLuX/venv/bin
ExecStart=/home/username/TeleLuX/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 第六步：启动服务

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start telex.service

# 设置开机自启
sudo systemctl enable telex.service

# 查看服务状态
sudo systemctl status telex.service
```

## 📊 监控和管理

### 查看日志
```bash
# 查看实时日志
sudo journalctl -u telex.service -f

# 查看最近的日志
sudo journalctl -u telex.service -n 50

# 查看应用日志文件
tail -f ~/TeleLuX/telex.log
```

### 管理服务
```bash
# 停止服务
sudo systemctl stop telex.service

# 重启服务
sudo systemctl restart telex.service

# 查看服务状态
sudo systemctl status telex.service

# 禁用开机自启
sudo systemctl disable telex.service
```

### 更新程序
```bash
# 停止服务
sudo systemctl stop telex.service

# 更新代码
cd ~/TeleLuX
# 如果使用git
git pull

# 或者重新上传文件

# 重启服务
sudo systemctl start telex.service
```

## 🔧 故障排除

### 常见问题

1. **服务启动失败**
```bash
# 查看详细错误信息
sudo journalctl -u telex.service -n 20
```

2. **Python模块找不到**
```bash
# 确保虚拟环境路径正确
which python
# 应该显示: /home/username/TeleLuX/venv/bin/python
```

3. **权限问题**
```bash
# 确保文件权限正确
sudo chown -R username:username ~/TeleLuX
chmod +x ~/TeleLuX/main.py
```

4. **网络连接问题**
```bash
# 测试网络连接
curl -I https://api.twitter.com
curl -I https://api.telegram.org
```

### 性能优化

1. **内存使用优化**
```bash
# 查看内存使用
free -h
top -p $(pgrep -f "python main.py")
```

2. **日志轮转**
```bash
# 创建日志轮转配置
sudo nano /etc/logrotate.d/telex

# 添加内容：
/home/username/TeleLuX/telex.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

## 🛡️ 安全建议

1. **防火墙配置**
```bash
# Ubuntu/Debian
sudo ufw enable
sudo ufw allow ssh

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

2. **定期备份**
```bash
# 创建备份脚本
cat > ~/backup_telex.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf ~/telex_backup_$DATE.tar.gz ~/TeleLuX
find ~ -name "telex_backup_*.tar.gz" -mtime +7 -delete
EOF

chmod +x ~/backup_telex.sh

# 添加到crontab（每天备份）
crontab -e
# 添加行：0 2 * * * /home/username/backup_telex.sh
```

## ✅ 部署完成检查清单

- [ ] VPS环境准备完成
- [ ] Python 3.8+安装成功
- [ ] 项目文件上传完成
- [ ] 虚拟环境创建成功
- [ ] 依赖包安装完成
- [ ] .env配置文件填写正确
- [ ] 程序测试运行成功
- [ ] systemd服务创建成功
- [ ] 服务启动并运行正常
- [ ] 开机自启设置完成
- [ ] 日志查看正常
- [ ] Telegram通知接收正常

## 🎉 恭喜！

你的TeleLuX系统现在已经成功部署到Oracle VPS上，将24/7自动运行！

如果遇到任何问题，请查看日志文件或联系技术支持。
