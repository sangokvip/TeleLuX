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
