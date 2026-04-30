import asyncio
import logging
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
from config import Config
from utils import utils

logger = logging.getLogger(__name__)

ORDER_BOT_URL = "https://t.me/lulaoshishop_bot"
ORDER_BOT_BUTTON_TEXT = "点击自助下单进群"

class TelegramNotifier:
    """Telegram通知类"""
    
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.bot = Bot(token=self.bot_token)

    def _create_order_bot_button(self):
        """创建跳转下单机器人的内联按钮。"""
        keyboard = [
            [InlineKeyboardButton(ORDER_BOT_BUTTON_TEXT, url=ORDER_BOT_URL)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def send_tweet_notification(self, username, tweet_text, tweet_url, created_at):
        """发送推文通知"""
        try:
            # 构建消息内容
            message = self._format_tweet_message(username, tweet_text, tweet_url, created_at)
            
            # 发送消息
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False,
                reply_markup=self._create_order_bot_button()
            )
            
            logger.info(f"成功发送推文通知: {tweet_url}")
            return True
            
        except TelegramError as e:
            logger.error(f"发送Telegram消息失败: {e}")
            return False
        except Exception as e:
            logger.error(f"发送通知时发生未知错误: {e}")
            return False
    
    def _format_tweet_message(self, username, tweet_text, tweet_url, created_at):
        """格式化推文消息"""
        # 限制推文文本长度
        max_text_length = 200
        if len(tweet_text) > max_text_length:
            tweet_text = tweet_text[:max_text_length] + "..."
        
        # 转义HTML特殊字符 - 使用utils模块
        tweet_text = utils.escape_html(tweet_text)
        safe_username = username if utils.is_safe_twitter_username(username) else Config.TWITTER_USERNAME
        safe_username = safe_username if utils.is_safe_twitter_username(safe_username) else "i"
        display_username = utils.escape_html(username)
        safe_tweet_url = tweet_url if utils.is_safe_twitter_url(tweet_url) else f"https://x.com/{safe_username}"
        
        message = f"""
🐦 <b>新推文提醒</b>

👤 <b>用户:</b> <a href="https://x.com/{safe_username}">@{display_username}</a>
📝 <b>内容:</b> {tweet_text}
🕒 <b>时间:</b> {utils.escape_html(str(created_at))}

🔗 <a href="{safe_tweet_url}">查看原推文</a>
        """.strip()
        
        return message
    
    def _escape_html(self, text):
        """转义HTML特殊字符 - 已弃用，请直接使用utils.escape_html()"""
        # 为了向后兼容，调用utils模块的函数
        import warnings
        warnings.warn("_escape_html方法已弃用，请使用utils.escape_html()", DeprecationWarning, stacklevel=2)
        return utils.escape_html(text)
    
    async def send_status_message(self, message):
        """发送状态消息"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"🤖 <b>监控状态</b>\n\n{message}",
                parse_mode='HTML'
            )
            logger.info("状态消息发送成功")
            return True
        except Exception as e:
            logger.error(f"发送状态消息失败: {e}")
            return False
    
    async def test_connection(self):
        """测试Telegram连接"""
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Telegram Bot连接成功: {bot_info.username}")
            return True
        except Exception as e:
            logger.error(f"Telegram Bot连接失败: {e}")
            return False

# 同步包装器函数
def send_tweet_notification_sync(username, tweet_text, tweet_url, created_at):
    """同步发送推文通知"""
    notifier = TelegramNotifier()
    return asyncio.run(notifier.send_tweet_notification(username, tweet_text, tweet_url, created_at))

def send_status_message_sync(message):
    """同步发送状态消息"""
    notifier = TelegramNotifier()
    return asyncio.run(notifier.send_status_message(message))

def test_telegram_connection():
    """测试Telegram连接"""
    notifier = TelegramNotifier()
    return asyncio.run(notifier.test_connection())

class TelegramBotListener:
    """Telegram机器人监听器类"""

    def __init__(self, twitter_monitor=None):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.twitter_monitor = twitter_monitor
        self.application = None

    def _create_order_bot_button(self):
        """创建跳转下单机器人的内联按钮。"""
        keyboard = [
            [InlineKeyboardButton(ORDER_BOT_BUTTON_TEXT, url=ORDER_BOT_URL)]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理收到的消息"""
        try:
            message_text = update.message.text.strip()
            chat_type = update.effective_chat.type
            chat_id = update.effective_chat.id
            user_name = update.effective_user.username or update.effective_user.first_name

            logger.info(f"收到消息: '{message_text}' 来自: {user_name} (Chat ID: {chat_id}, 类型: {chat_type})")

            # 处理私聊消息
            if chat_type == 'private':
                # 检查是否是特定的触发消息"27"
                if message_text == "27":
                    special_message = """小助理下单机器人： 👉https://t.me/lulaoshishop_bot

※平台是自助入群，机器人下单即可。

如果不太会使用平台，或者遇到任何问题，可以私信我，或者私信露老师截图扫码支付：@mteacherlu。

除门槛相关露老师个人电报私信不接受闲聊，禁砍价，不强迫入门，也请保持基本礼貌，感谢理解。

注意事项：
1.露老师不做线下服务，如果有线下相关问题，请私信我询问。
2.因个人原因退群后不再重新拉群，还请注意一下。
3.支付过程中如有任何问题，也欢迎私信我，我会尽力帮助。

感谢大家的配合和支持！✨

---------------------------------------------------

相关群组与定制介绍：

日常群：稳定更新，露老师个人原创作品，会更新长视频以及多量照片，都是推特所看不到的内容。

女女群：稳定更新，除露老师外还可以看到另外几位女主，露老师与其他女主合作视频等。

三视角群：不定期更新，每次活动拍摄由男友视角随心拍摄。

定制视频：根据需求定制露老师视频，可SOLO、FM、FF、FFM、FMM，可按要求使用各种玩具和剧情设计。

※希望得到更详细介绍询问请私信"""

                    # 发送到配置的群组
                    await context.bot.send_message(
                        chat_id=self.chat_id,
                        text=special_message,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )

                    # 给私聊用户发送确认消息
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="✅ 已向群组发送相关信息",
                        parse_mode='HTML'
                    )

                    logger.info(f"收到私聊触发词'27'，已向群组发送业务介绍消息 (来自用户: {user_name})")
                    return
                else:
                    # 对其他私聊消息给予提示
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="👋 你好！如需发送业务介绍到群组，请发送 '27'",
                        parse_mode='HTML'
                    )
                    logger.info(f"收到私聊消息'{message_text}'，已回复提示信息 (来自用户: {user_name})")
                    return

            # 处理群组消息（原有功能）
            elif str(chat_id) == str(self.chat_id):
                # 获取监控用户的最新推文
                if self.twitter_monitor:
                    username = Config.TWITTER_USERNAME
                    logger.info(f"群组消息触发，获取 @{username} 的最新推文...")

                    latest_tweets = await self.twitter_monitor.get_latest_tweets(username, count=1)

                    if latest_tweets:
                        tweet = latest_tweets[0]

                        # 发送最新推文
                        safe_username = username if utils.is_safe_twitter_username(username) else "i"
                        safe_tweet_url = tweet.get('url') if utils.is_safe_twitter_url(tweet.get('url')) else f"https://x.com/{safe_username}"

                        message = f"""
🐦 <b><a href="https://x.com/{safe_username}">@{utils.escape_html(username)}</a> 的最新推文</b>

📝 <b>内容:</b> {utils.escape_html(tweet['text'])}
🕒 <b>时间:</b> {tweet['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}

🔗 <a href="{safe_tweet_url}">查看原推文</a>
                        """.strip()

                        await context.bot.send_message(
                            chat_id=self.chat_id,
                            text=message,
                            parse_mode='HTML',
                            disable_web_page_preview=False,
                            reply_markup=self._create_order_bot_button()
                        )

                        logger.info("成功发送最新推文")
                    else:
                        await context.bot.send_message(
                            chat_id=self.chat_id,
                            text=f"⚠️ 暂时无法获取 @{username} 的推文",
                            parse_mode='HTML'
                        )
                else:
                    await context.bot.send_message(
                        chat_id=self.chat_id,
                        text="⚠️ Twitter监控服务未初始化",
                        parse_mode='HTML'
                    )
            else:
                # 忽略其他群组的消息
                logger.info(f"忽略来自其他群组的消息: {chat_id}")

        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")
            try:
                # 根据消息来源发送错误提示
                if update.effective_chat.type == 'private':
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ 处理消息时发生错误",
                        parse_mode='HTML'
                    )
                else:
                    await context.bot.send_message(
                        chat_id=self.chat_id,
                        text="❌ 处理消息时发生错误",
                        parse_mode='HTML'
                    )
            except:
                pass

    def _escape_html(self, text):
        """转义HTML特殊字符"""
        if not text:
            return ""

        html_escape_table = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }

        return "".join(html_escape_table.get(c, c) for c in text)

    async def start_listening(self):
        """开始监听消息"""
        try:
            logger.info("启动Telegram机器人监听...")

            # 创建应用
            self.application = Application.builder().token(self.bot_token).build()

            # 添加消息处理器
            message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            self.application.add_handler(message_handler)

            # 启动机器人
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            logger.info("Telegram机器人监听已启动")

        except Exception as e:
            logger.error(f"启动Telegram机器人监听失败: {e}")
            raise

    async def stop_listening(self):
        """停止监听"""
        try:
            if self.application:
                logger.info("停止Telegram机器人监听...")
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram机器人监听已停止")
        except Exception as e:
            logger.error(f"停止Telegram机器人监听失败: {e}")

# 全局变量用于存储监听器实例
_bot_listener = None

def start_bot_listener(twitter_monitor):
    """启动机器人监听器（同步版本）"""
    global _bot_listener
    try:
        _bot_listener = TelegramBotListener(twitter_monitor)
        asyncio.run(_bot_listener.start_listening())
    except Exception as e:
        logger.error(f"启动机器人监听器失败: {e}")

def stop_bot_listener():
    """停止机器人监听器（同步版本）"""
    global _bot_listener
    if _bot_listener:
        try:
            asyncio.run(_bot_listener.stop_listening())
        except Exception as e:
            logger.error(f"停止机器人监听器失败: {e}")
        finally:
            _bot_listener = None
