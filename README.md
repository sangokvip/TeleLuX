# TeleLuX

TeleLuX 是一个增强版 Twitter 监控和 Telegram 通知系统，能够自动监控指定 Twitter 账号的新推文并发送到 Telegram 群组，同时支持私信触发特定功能。

## 功能特性

- 🐦 **自动监控 Twitter 推文**：定期检查指定账号的新推文
- 📱 **Telegram 通知**：将新推文自动发送到指定的 Telegram 群组
- 💬 **私信触发功能**：私聊机器人发送"27"自动发送业务介绍到群组
- 🔍 **群组消息触发**：在群组发送任意消息获取最新推文
- 💾 **智能去重**：避免重复发送相同的推文
- 🔄 **自动重试**：网络错误时自动重试
- 📊 **日志记录**：详细的运行日志
- 🛡️ **错误恢复**：异常情况下自动恢复运行

## 快速开始

### 1. 环境准备

确保你的系统已安装 Python 3.8+：

```bash
python --version
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

编辑 `.env` 文件：

```env
# Twitter API 配置
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# Telegram 配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# 监控配置
TWITTER_USERNAME=target_username_without_@
CHECK_INTERVAL=3000
```

### 4. 运行系统

```bash
python main.py
```

## 功能说明

### 🔥 核心功能

1. **自动推文监控**
   - 每50分钟自动检查新推文
   - 发现新推文时自动发送到群组
   - 智能去重，避免重复通知

2. **私信业务触发**
   - 私聊机器人发送"27"
   - 自动向群组发送完整业务介绍
   - 私聊收到确认消息

3. **群组消息触发**
   - 在群组中发送任意消息
   - 机器人自动回复最新推文内容和链接

### 🎯 使用方法

- **获取最新推文**：在群组中发送任意消息
- **发送业务介绍**：私聊机器人发送"27"
- **自动通知**：系统会自动监控并通知新推文

## 配置说明

### Twitter API 配置

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建一个新的应用
3. 获取 Bearer Token
4. 将 Bearer Token 填入 `.env` 文件

### Telegram Bot 配置

1. 与 [@BotFather](https://t.me/botfather) 对话创建新机器人
2. 获取 Bot Token
3. 将机器人添加到目标群组
4. 获取群组 Chat ID

### 监控配置

- `TWITTER_USERNAME`: 要监控的 Twitter 用户名（不包含 @）
- `CHECK_INTERVAL`: 检查间隔（秒），建议 3000 秒（50分钟）

### 环境变量

| 变量名 | 必需 | 说明 | 默认值 |
|--------|------|------|--------|
| `TWITTER_BEARER_TOKEN` | ✅ | Twitter API Bearer Token | - |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram机器人Token | - |
| `TELEGRAM_CHAT_ID` | ✅ | Telegram群组/频道ID | - |
| `TWITTER_USERNAME` | ✅ | 监控的Twitter用户名 | - |
| `CHECK_INTERVAL` | ❌ | 检查间隔（秒） | 3000 |

## 项目结构

```
TeleLuX/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── twitter_monitor.py   # Twitter 监控模块
├── telegram_bot.py      # Telegram 机器人模块
├── database.py          # 数据库管理
├── requirements.txt     # 依赖包列表
├── .env                 # 环境变量配置
├── tweets.db           # SQLite 数据库文件
├── telex.log           # 系统日志文件
└── README.md           # 项目说明
```

## 使用说明

### 启动系统

```bash
python main.py
```

系统启动后会：
1. 验证配置
2. 初始化数据库
3. 开始监控 Twitter
4. 启动 Telegram 机器人
5. 发送启动通知到 Telegram

### 停止系统

按 `Ctrl+C` 停止系统，系统会：
1. 发送停止通知
2. 清理资源
3. 安全退出

### 查看日志

系统会在控制台和 `telex.log` 文件中记录详细日志。

## 故障排除

### 常见问题

1. **Twitter API 错误**
   - 检查 Bearer Token 是否正确
   - 确认 API 配额未超限

2. **Telegram 发送失败**
   - 检查 Bot Token 是否正确
   - 确认机器人已添加到群组
   - 验证 Chat ID 是否正确

3. **私信功能不工作**
   - 确认机器人隐私设置允许接收私信
   - 检查机器人是否正常运行

4. **群组消息功能不工作**
   - 给机器人管理员权限
   - 或调整机器人隐私设置

### 获取帮助

如果遇到问题，请：
1. 查看日志文件 `telex.log`
2. 检查配置是否正确
3. 确认网络连接正常

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
