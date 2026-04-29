# TeleLuX 安全与功能审查报告

审查日期：2026-04-29

审查范围：`main.py`、`twitter_monitor.py`、`telegram_bot.py`、`standalone_reply_bot.py`、`database.py`、`utils.py`、`.env.example`、部署脚本和依赖文件。未读取 `.env`、`env.txt`、`damabluechaiENV.txt` 的真实内容。

## 总体结论

当前项目能完成 Telegram 群管理、推文转发、私信转发、自动回复、入群验证和黑名单等核心功能，但安全基线偏弱，主要风险集中在密钥管理、HTML 输出转义、管理员权限校验、第三方接口容错和部署可重复性。

优先级建议：

| 优先级 | 事项 | 原因 |
|---|---|---|
| P0 | 轮换 `.env.example` 中疑似真实 Twitter 凭据，清理历史提交 | 一旦仓库外泄，可直接导致 API 凭据被滥用 |
| P0 | 修复所有 HTML parse_mode 下未转义字段 | Telegram HTML 解析异常会导致消息发送失败，也可能产生链接/展示注入 |
| P1 | 管理员身份改为 `user.id` allowlist，并限制 polling updates | 减少误授权和无关 update 处理面 |
| P1 | 修复旧入口异步调用错误与重复机器人代码 | 避免备用路径上线后直接失效或行为不一致 |
| P2 | 加强依赖锁定、systemd 沙箱、日志脱敏、监控告警 | 提升线上稳定性和运维可控性 |

## 安全发现

### S1. `.env.example` 包含疑似真实 Twitter 凭据

位置：`.env.example:3-7`

`.env.example` 中的 Twitter Bearer Token、API Key、API Secret、Access Token Secret 看起来不是占位符。即使这些凭据已失效，也应按泄露处理。

影响：

- 第三方可能调用 Twitter/X API 或消耗额度。
- 凭据进入 Git 历史后，删除当前文件内容不足以消除风险。
- `git ls-files` 显示 `.env.example` 已被版本管理跟踪。

建议：

1. 立即在 Twitter/X Developer Portal 轮换或吊销相关凭据。
2. 将 `.env.example` 改成纯占位符。
3. 使用 `git filter-repo` 或 BFG 清理历史中的密钥。
4. 增加 `detect-secrets` 或 `gitleaks` 到本地/CI。
5. 将 `env.txt`、`damabluechaiENV.txt`、`*.env`、`*.db`、`_temp_archive/` 加入 `.gitignore`，并清理已跟踪的 `tweets.db` 和 `_temp_archive`。

### S2. 多处 HTML 输出未完整转义

位置：

- `main.py:135-139` 管理员回复内容直接以 HTML 发送。
- `main.py:387` `tweet_info['username']` 同时出现在 HTML href 和文本中。
- `main.py:392` `tweet_info['url']` 直接进入 href。
- `main.py:563-567` 黑名单字段 `username`、`reason` 未转义。
- `main.py:1493-1500` 自动推文中的 `username`、`tweet['url']` 未转义。
- `standalone_reply_bot.py:161-176` `query.from_user.first_name` 未转义。

影响：

- 第三方 API 或用户可控字段中如果包含 `<`、`"`、`&` 等字符，Telegram HTML 解析可能失败，导致消息无法发送。
- href 未做 URL allowlist 校验时，存在展示层链接注入风险。

建议：

1. 建立统一的 `safe_html_text()` 和 `safe_telegram_url()`。
2. 所有 HTML 文本字段用 `utils.escape_html()`。
3. URL 字段只允许 `https://twitter.com/`、`https://x.com/`、`https://t.me/`、`https://web.telegram.org/` 等明确域名。
4. 管理员回复建议不使用 HTML，或对回复内容先转义。

### S3. 管理员权限只基于私聊 `chat_id`

位置：`main.py:110-119`，`standalone_reply_bot.py:99-101`、`standalone_reply_bot.py:190-192`

当前主程序通过 `ADMIN_CHAT_ID` 与当前私聊 `chat_id` 相等来判断管理员。Telegram 私聊中 `chat_id` 通常等于用户 ID，但安全语义上应显式校验 `update.effective_user.id`，并支持 allowlist。

影响：

- 权限模型不清晰，后续扩展多管理员或群内管理命令时容易误用。
- 独立回复机器人也存在类似校验，且 `/reply` 的目标 ID 未校验格式。

建议：

1. 新增 `ADMIN_USER_IDS=123,456`。
2. 所有管理命令统一走 `is_admin(update)`。
3. `target_chat_id` 只接受整数 ID，禁止任意字符串。
4. 管理命令加审计日志，记录管理员 ID、命令、目标用户。

### S4. 第三方接口响应内容直接参与业务输出

位置：`twitter_monitor.py:239-286`，`main.py:375-392`

单推文详情来自 `api.vxtwitter.com`，返回的 `tweetURL`、`user_screen_name`、`thumbnail_url` 被下游直接用于 Telegram 消息、图片发送和链接展示。

影响：

- 第三方接口结构变化或异常数据会导致转发失败。
- 图片 URL 如果不是 HTTPS 或不是预期域名，可能触发 Telegram 拉取未知资源。

建议：

1. 对 `tweet_id` 做数字校验。
2. 对 `tweetURL`、`preview_image_url` 做 URL 解析和域名 allowlist。
3. 给 `get_tweet_by_id()` 增加 `timeout`，当前 VxTwitter 请求未设置超时。
4. 对第三方字段设置默认值和长度上限。

### S5. 启动 polling 订阅所有 Update 类型

位置：`main.py:1898-1900`

`allowed_updates=Update.ALL_TYPES` 会接收当前业务不需要的 update 类型。

影响：

- 扩大处理面和日志噪音。
- 未来新增 handler 时更容易误处理不需要的 Telegram 事件。

建议：

只订阅当前需要的类型，例如 `message`、`chat_member`、`callback_query`。

### S6. 依赖未完全锁定

位置：`requirements.txt:4`

`aiohttp` 未固定版本。部署脚本中的依赖和当前 `requirements.txt` 也不一致，仍包含 `requests`、`schedule`，但主程序已改为 `aiohttp`。

影响：

- 新部署环境可能安装到行为不兼容或有安全问题的版本。
- 脚本部署出来的环境可能缺少 `aiohttp`。

建议：

1. 固定 `aiohttp` 版本。
2. 移除未使用依赖，或解释保留原因。
3. 生成 `requirements.lock` 或使用 `pip-tools`。
4. 定期运行 `pip-audit`。

## 功能与稳定性发现

### F1. `telegram_bot.py` 备用入口调用 async 方法但未 await

位置：`telegram_bot.py:217`

`self.twitter_monitor.get_latest_tweets()` 是 async 方法，这里直接赋值，得到的是 coroutine，不是列表。若启用该备用监听器，群组触发获取最新推文会失效。

建议：

- 将调用改为 `latest_tweets = await self.twitter_monitor.get_latest_tweets(...)`。
- 或删除旧入口，统一只保留 `main.py`。

### F2. 主程序和旧机器人/独立回复机器人功能重复

位置：`main.py`、`telegram_bot.py`、`standalone_reply_bot.py`

项目存在三个 Telegram 入口，私信转发、推文发送、业务介绍等逻辑重复，且实现不一致。

影响：

- 修一个入口容易漏另一个入口。
- 部署时不清楚哪一个是生产入口。
- 独立回复机器人里“标记可疑”只改消息文本，没有持久化或风控动作。

建议：

1. 明确 `main.py` 为唯一生产入口。
2. 将旧入口移到 `legacy/` 或删除。
3. 提取共享服务：`telegram_messages.py`、`tweet_formatter.py`、`admin_auth.py`。

### F3. 推文去重先标记后发送

位置：`twitter_monitor.py:295-326`，`main.py:1478-1532`

`check_new_tweets()` 在返回前已将新推文标记为 processed。如果后续 Telegram 发送失败，该推文不会再次发送。

建议：

- 将“发现新推文”和“标记已发送”拆开。
- 只有 Telegram 发送成功后再写入 processed。
- 表结构增加 `status`、`send_attempts`、`last_error`。

### F4. 入群验证允许新用户继续发送文本

位置：`main.py:1235-1256`

验证限制设置了 `can_send_messages=True`，这样用户在验证前仍能发送普通文本，只是不能发媒体和链接预览。

建议：

- 如果目标是防刷屏，应设置 `can_send_messages=False`，通过私聊验证或按钮验证完成后恢复。
- 如果保留群内回答数学题，则需配合只允许验证码消息，并删除其他消息。

### F5. 黑名单不会自动阻止再次进群

位置：`database.py:126-134`，`main.py:758-880`

加入事件中未查询 `is_user_blacklisted()` 并踢出或通知管理员。

建议：

- 用户加入时先查黑名单。
- 黑名单命中后立即移除，并通知管理员。
- 增加手动 `ban 用户ID 原因` 命令。

### F6. 日志和统计只保存在内存

位置：`main.py:45-54`、`main.py:1442-1452`

机器人重启后统计、活动日志、欢迎消息 ID、业务介绍消息 ID 都会丢失。

建议：

- 将关键运行状态放入 SQLite。
- 业务介绍消息 ID 持久化，重启后仍能删除上一条。
- 日志表保留最近 7-30 天。

### F7. 部署脚本与当前代码脱节

位置：`deploy_script.sh:26-33`、`quick_deploy.sh:35-39`、`requirements.txt:1-4`

部署脚本会生成一套旧依赖，可能缺少当前主程序需要的 `aiohttp`。`quick_deploy.sh` 还会生成旧版 `config.py`。

建议：

- 删除会生成旧代码的 `quick_deploy.sh`，或改成只拉取仓库并安装当前依赖。
- `deploy_script.sh` 使用仓库内 `requirements.txt`。
- 增加 systemd 安全配置：`NoNewPrivileges=true`、`PrivateTmp=true`、`ProtectSystem=strict`、`ReadWritePaths=$PROJECT_DIR`。

## 优化计划

### 第 1 阶段：安全止血

| 任务 | 文件 | 验证 |
|---|---|---|
| 轮换泄露凭据，替换 `.env.example` 为占位符 | `.env.example` | `gitleaks detect` |
| 清理 Git 历史中的密钥和数据库文件 | Git 历史 | 新 clone 后搜不到旧密钥 |
| 所有 Telegram HTML 输出统一转义 | `main.py`、`standalone_reply_bot.py`、`telegram_bot.py` | 构造包含 `<>&"` 的用户/推文字段测试 |
| 管理员认证统一封装 | `main.py`、`standalone_reply_bot.py` | 非管理员命令全部拒绝 |

### 第 2 阶段：稳定性修复

| 任务 | 文件 | 验证 |
|---|---|---|
| 修复去重状态，发送成功后再标记 | `twitter_monitor.py`、`main.py`、`database.py` | 模拟 Telegram 发送失败后下次仍会重试 |
| 修复 `telegram_bot.py` async 调用或移除旧入口 | `telegram_bot.py` | `python3 -m py_compile` + 单元测试 |
| 第三方 URL allowlist 与超时 | `twitter_monitor.py`、`utils.py` | 异常 URL 被拒绝，超时不阻塞主循环 |
| 黑名单用户入群自动处理 | `main.py`、`database.py` | 黑名单用户加入时自动移除 |

### 第 3 阶段：工程化

| 任务 | 文件 | 验证 |
|---|---|---|
| 统一配置 schema 和部署脚本 | `config.py`、`deploy_script.sh`、`quick_deploy.sh` | 新 VPS 从零部署成功 |
| 依赖锁定和安全扫描 | `requirements.txt`、`requirements.lock` | `pip-audit` 无高危 |
| 状态持久化 | `database.py`、`main.py` | 重启后统计和业务介绍消息 ID 保留 |
| 自动测试覆盖核心逻辑 | `tests/` | URL 解析、权限、转义、去重测试通过 |

## 建议的验收命令

```bash
python3 -m py_compile main.py telegram_bot.py standalone_reply_bot.py twitter_monitor.py database.py utils.py config.py
python3 -m json.tool docs/worklogs/2026-04-29-tweet-order-button.json >/dev/null
gitleaks detect --source .
pip-audit -r requirements.txt
```

