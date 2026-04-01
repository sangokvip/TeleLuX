# CASCADE WORKLOG

### 1) Fix: 修复定时业务介绍群发消息功能失效
- **变更文件**: `main.py`
- **背景与目标**: 每8小时自动发送群消息的功能完全失效，用户报告该功能不工作
- **技术实施**:
  - 修复 `check_business_intro_schedule` 函数中的缩进/逻辑 bug：消息定义和发送代码原本被错误地放在 `else`（首次运行）分支内，导致后续调用即使超过时间间隔也永远不会执行发送逻辑
  - 将消息发送逻辑移至 `if/else` 判断之后的统一层级，确保首次运行和后续运行都能在超时后正确触发发送
  - 将发送间隔从 10800 秒（3小时）修正为 28800 秒（8小时），与用户需求保持一致
  - 简化首次运行逻辑：首次启动时记录时间但不立即发送，等待8小时后首次发送
- **风险自查**:
  - 消息内容未做任何修改，仅修正了代码结构和间隔时间
  - 已验证修复后的缩进和控制流逻辑正确
  - 不影响手动触发（私聊发送"27"）的业务介绍发送功能
- **回滚点**: `git diff HEAD -- main.py` 可查看变更，`git checkout HEAD -- main.py` 可回滚

### 2) Style: 移除群欢迎消息中的进群指引
- **变更文件**: `main.py`
- **背景与目标**: 用户要求删除进群欢迎消息中关于“telegram进群后不显示内容”的大段解决办法提示，以精简欢迎消息
- **技术实施**:
  - 在 `handle_chat_member` 函数中，修改 `welcome_message` 的字符串模板
  - 删除了以"📌 <b>重要提示：</b>如果您进群后不显示内容..."开头的4条解决办法步骤
  - 保持了上方的欢迎语、账号认证和防骗提示不变
- **风险自查**:
  - 仅修改了字符串模板内容，不影响消息发送逻辑
  - 移细了包含外部链接的 HTML 标签，减少了可能被判定为广告的风险
- **回滚点**: `git diff HEAD -- main.py` 可查看变更，`git checkout HEAD -- main.py` 可回滚

### 3) Feature: 提升群用户转化机制（内联按钮与引导话术）
- **变更文件**: `main.py`
- **背景与目标**: 用户希望提供更好的方法，让现有的免费群用户主动进入付费群，提升购买转化率
- **技术实施**:
  - 引入了 `telegram.InlineKeyboardButton` 和 `InlineKeyboardMarkup`，在“业务介绍”消息（包括定时发送和“27”口令触发版）下方，增加了一个名为“👉 点击这里购买/了解价格”的内联按钮。相比纯文本链接，内联按钮具有更高的视觉吸引力和点击率。
  - 将 `auto_replies`（针对“怎么进群”、“求进群”等触发词自动回复）的文案从原本生硬的一句话链接，改为带有营销引导性质的文案：“想要解锁更多专属内容吗？🤫\n目前有【视频课堂群】和【女女群】等多种选择哦！\n👉 请点击这里直接和下单机器人了解价格：...”。
- **风险自查**:
  - 导入新模块没有覆盖原有的任何模块。
  - 创建 InlineKeyboardButton 时确保遵循了 `python-telegram-bot` API 的基本语法，传递了正确的 `url` 参数和 `reply_markup` 参数给 `send_message`。
- **回滚点**: `git diff HEAD -- main.py` 可查看变更，`git checkout HEAD -- main.py` 可回滚

### 4) Feature: 自动回复增加内联大按钮跳转
- **变更文件**: `main.py`
- **背景与目标**: 用户在测试后，要求对触发关键词的自动回复也采用内联大按钮跳转的方式，以进一步优化引导转化。
- **技术实施**:
  - 更新了 `self.auto_replies` 字典中的文本，删除了硬编码的下订单链接（URL），仅保留引导语。
  - 在处理私聊自动回复（约 435 行）以及处理群聊自动回复（约 487 行）的地方，生成了统一的 `InlineKeyboardMarkup` 包含按钮 `👉 点击这里直接与下单机器人了解价格` 并指向 `https://t.me/Lulaoshi_bot`。
  - 将 `reply_markup=reply_markup` 显式传递给了对应的 `context.bot.send_message` 函数。
- **风险自查**:
  - 移除了字典里的硬链接，保持内容与表示层的分离。
  - 已检查 python-telegram-bot 发送方法的签名，添加 `reply_markup` 参数不会影响既有功能。
- **回滚点**: `git diff HEAD -- main.py` 可查看变更，`git checkout HEAD -- main.py` 可回滚

### 5) Refactor: 替换失效的 Twitter(X) Free API 为 RapidAPI
- **变更文件**: `config.py`、`twitter_monitor.py`、`main.py`、`requirements.txt`
- **背景与目标**: Twitter 收回了官方原有的 Free API 数据读取权限（引发 403 错误），为保全自动推送推文功能，迁移至 RapidAPI 上的非官方接口引擎 (Twtttr API)。
- **技术实施**:
  - 更新配置：在 `config.py` 及校验逻辑中加入并置顶 `RAPIDAPI_KEY`，弃用原有的 tweepy 配置参数验证。
  - 更换依赖库：添加 `aiohttp` 以支持非阻塞的并发网络请求，移除官方封闭的 `tweepy`。
  - 重构监控类：`TwitterMonitor` 完成底层重写，内部请求使用 `_make_request(url, headers)` 进行。
  - 定制解析：由于新接口使用了逆向内网接口返回庞杂的 GraphQL 层级 JSON，重新实现了 `get_latest_tweets` 利用 `TimelineAddEntries` 定位推文。
  - 同步转异步适配：对 `TeleLuxBot (main.py)` 中此前对推文类的调用改为 `await` 异步访问，防止阻塞主 loop。
- **风险自查**:
  - 移除原先的 tweepy 相关配置报错将不再打断启动。
  - 使用了 try-catch 全面包裹 HTTP 访问请求，避免网络断层拖垮 bot 本体。
- **回滚点**: `git stash / git checkout .` 撤销本次代码结构更改。

### 3) Fix: 修复推文直链解析的异步错误
- **变更文件**: `main.py`, `twitter_monitor.py`
- **背景与目标**: 将 `get_tweet_by_id` 等方法改为异步后，主流程中调用仍用了已废弃的同步线程包装导致返回 coroutine 错误，且新的 API 不支持直接按 ID 查推，需要用户名做前缀扫描。
- **技术实施**:
  - 移除 `run_in_thread(get_tweet_by_id...)` 改为直接 `await self.twitter_monitor.get_tweet_by_id`。
  - 在 `main.py` 处理特定 URL 的逻辑里，增加提取 URL 里面的 `username` 并传给后台检索。
  - 在 `twitter_monitor.py` 中的 `get_tweet_by_id` 实现近期推文循环比对的功能，通过传入的 `username` 先拉列表再做特征命中。
- **风险自查**:
  - 仅限于处理单个推文详情链接回复，不影响自动监控循环。
- **回滚点**: 

### 4) Fix: 修复抓取日志网络请求属性及 admin_chat_id 抛错
- **变更文件**: `twitter_monitor.py`, `main.py`
- **背景与目标**: 用户反馈线上版本抛出 `name 'url' is not defined` 以及 `TeleLuXBot object has no attribute admin_chat_id`。前者是因为替换新 API 发包类重组时不慎漏写了组装 url 变量的逻辑；后者是 Bot 实例在 `__init__` 漏写了属性绑定。
- **技术实施**:
  - 恢复 `_make_request` 中的 `url = f'https://twitter241...{endpoint}'`。
  - 在 `TeleLuXBot.__init__` 补充 `self.admin_chat_id = Config.ADMIN_CHAT_ID`。
- **风险自查**:
  - 仅修补运行时上下文漏洞。
- **回滚点**: 

### 5) Fix: 修正 twitter241 端点参数名及解析路径
- **变更文件**: `twitter_monitor.py`
- **背景与目标**: 日志显示推文抓取依然失败，显示 "在近期推文中未找到..."。通过直接测试端点发现：`twitter241` 的 `/user-tweets` 实际要求的参数名是 `user` 而非 `user_id`，如果不传 `user` 会报出的 strconv 错误导致返回空结果，且返回的 JSON 结构中 timeline 的层级也有所不同。
- **技术实施**:
  - 将 `get_latest_tweets` 中的请求参数 `user_id` 改为 `user`。
  - 更新解析路径为 `data['result']['timeline']['instructions']` 以匹配实际 API 返回。
  - 为推文结果提取增加对嵌套 `tweet` 字段的兼容处理。
- **风险自查**:
  - 经过多轮实测，已成功提取到指定用户的推文列表和 ID，确认逻辑闭环。
- **回滚点**: 

### 6) Feature: 彻底重构单推文获取 (接入 VxTwitter API)
- **变更文件**: `twitter_monitor.py`
- **背景与目标**: `twitter241` API 无法直接通过 ID 获取单条推文，原先采用的“拉取最新 Timeline 暴力查找”方式，若用户发送的推文较老（例如 5 天前）或者非常活跃，推文很容易直接被漏掉导致经常出现“未找到该推文”。因此，我找到了业界常用的免费全开放 API (api.vxtwitter.com)，实现单推文精准直取。
- **技术实施**:
  - 重写了 `get_tweet_by_id` 方法。
  - 使用 `aiohttp` 访问 `https://api.vxtwitter.com/Twitter/status/{tweet_id}` 接口。
  - 适配了其特有的 `media_extended` 媒体字段、`date_epoch` 时间戳以及基本文案返回信息，转为原有格式的 `tweet_info`。
- **风险自查**:
  - 返回结构的键名 (`id, text, created_at, url, username, media`) 均与原有 `get_latest_tweets` 保持绝对一致，与 `main.py` 无缝兼容。
- **回滚点**: 

### 7) Fix: 修复转发推文缺失预览图的问题
- **变更文件**: `twitter_monitor.py`
- **背景与目标**: 用户反馈转发推文时不显示视频预览图。经核查，新接入的 `get_tweet_by_id` 方法中缺少了 `preview_image_url` 字段，导致主程序退化为发送纯文本消息。
- **技术实施**:
  - 在 `get_tweet_by_id` 中从 `media_extended` 提取 `thumbnail_url` 并映射至顶层字段。
  - 增强了 `get_latest_tweets` 的解析逻辑，支持解析 `TweetWithVisibilityResults` 嵌套结构，提升自动化监控的稳定性。
- **风险自查**: 已通过测试脚本验证 VxTwitter 接口返回的预览图链接正常工作。
- **回滚点**: 

### 8) Chore: 调整推文监控频率与自动转发限制
- **变更文件**: `config.py`, `main.py`, `.env`
- **背景与目标**: 为了节省 RapidAPI 每月 500 次的免费额度并优化群组消息密度，用户希望改为每天检查一次推文，且每次只发送最新的前三条。
- **技术实施**:
  - 将 `CHECK_INTERVAL` 默认值及环境变量统一修改为 `86400` (24小时)。
  - 修改 `main.py` 中的 Twitter 监控循环，对获取到的新推文列表进行切片操作 (`new_tweets[:3]`)，仅处理前三条。
- **风险自查**: 已验证环境变量覆盖逻辑和代码切片逻辑正常工作。
- **回滚点**: 

### 9) Security: 修复凭证泄露导致的机器人被控问题
- **变更文件**: `env.txt`, `damabluechaiENV.txt`, `.gitignore`
- **背景与目标**: 机器人被恶意他人控制发送广告。经查是因为包含 Token 的配置文件被追踪进 Git 仓库导致泄露。需立即移除 Git 跟踪并加强忽略规则。
- **技术实施**:
  - 使用 `git rm --cached` 将 `env.txt` 和 `damabluechaiENV.txt` 从 Git 索引中移除（保留本地文件）。
  - 确认 `.gitignore` 中已包含上述文件，防止再次被提交。
  - 建议用户立即通过 @BotFather 撤销旧 Token 并更换新 Token。
- **风险自查**: 
  - 本次操作仅涉及 Git 索引管理，不影响本地文件内容和 VPS 运行。
  - 已验证执行后 `git ls-files` 不再包含上述文件。
- **回滚点**: `git add env.txt damabluechaiENV.txt` 可恢复跟踪（不建议）。

### 10) Security: 限制推文链接自动分享权限
- **变更文件**: `config.py`, `main.py`
- **背景与目标**: 为了进一步提升安全性，限制只有特定账号（mteacherlu, bryansuperb）发送的 Twitter 链接才会被机器人自动处理并转发到群组。其他用户发送的链接仅会被转发给管理员。
- **技术实施**:
  - 在 `config.py` 中增加 `ALLOWED_USERNAMES` 配置项，默认包含两个授权账号。
  - 在 `main.py` 的 `handle_message` 方法中增加逻辑判断：检测到 Twitter URL 后校验发送者 `username`。
  - 非授权用户发送的链接将跳过自动处理流程，保留既有的“私信转发管理员”机制。
- **风险自查**: 
  - 默认已处理用户名大小写不敏感匹配。
  - 已验证非授权用户发送的内容仍能通过既有逻辑转发给管理员，不会丢失消息。
- **回滚点**: `git checkout HEAD -- config.py main.py`
