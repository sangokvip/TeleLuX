#!/usr/bin/env python3
"""
TeleLuX - Twitter监控和Telegram通知系统
完整版系统，包含所有功能
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, ChatMemberHandler, filters, ContextTypes
from config import Config
from twitter_monitor import TwitterMonitor
from database import Database
from utils import utils, async_error_handler, run_in_thread

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TeleLuXBot:
    """TeleLuX完整版机器人"""
    
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.application = None
        self.twitter_monitor = None
        self.database = None
        self.last_check_time = None
        self.last_business_intro_time = None
        self.last_business_intro_message_id = None
        self.last_twitter_check_time = None  # Twitter监控上次检查时间
        # 免费API限额优化：默认8小时检查一次 (100条/月 ≈ 3次/天)
        self.twitter_check_interval = max(Config.CHECK_INTERVAL, 28800)  # 最小8小时
        self.twitter_api_calls_today = 0  # 今日API调用次数
        self.twitter_api_reset_date = datetime.now().date()  # API计数重置日期
        self.twitter_auto_forward_enabled = True  # 是否启用自动转发新推文
        # 统计数据
        self.stats = {
            'start_time': datetime.now(),
            'tweets_sent': 0,
            'welcome_sent': 0,
            'users_joined': 0,
            'users_left': 0,
            'commands_processed': 0,
            'errors': 0
        }
        # 使用内存管理器替代普通字典，防止内存无限增长
        from utils import MemoryManager
        self.user_activity_manager = MemoryManager(max_size=500, cleanup_threshold=0.8)
        self.welcome_messages = []  # 记录所有欢迎消息ID
        self.activity_logs = []  # 操作日志记录
        # 入群验证配置
        self.pending_verifications = {}  # 待验证用户 {user_id: {'expires': datetime, 'code': str}}
        self.verification_enabled = True  # 是否启用入群验证
        self.verification_timeout = 300  # 验证超时时间(秒)
        # 广告检测配置
        self.ad_keywords = [
            '加微信', '加v', '加V', 'wx:', 'WX:', '微信号', '微信：',
            '免费领取', '免费赠送', '点击链接', '点击进入',
            '赚钱', '日入', '月入', '日赚', '月赚', '轻松月入',
            '兑换码', '优惠券', '押金', '押金群',
            't.me/', 'telegram.me/', '@', 'http://', 'https://'
        ]
        self.ad_detection_enabled = True  # 是否启用广告检测
        # 智能回复配置
        self.auto_replies = {
            '价格': '💰 关于价格请私信露老师 @mteacherlu 或使用机器人 https://t.me/Lulaoshi_bot',
            '多少钱': '💰 关于价格请私信露老师 @mteacherlu 或使用机器人 https://t.me/Lulaoshi_bot',
            '怎么加入': '👉 请使用机器人下单 https://t.me/Lulaoshi_bot',
            '如何加入': '👉 请使用机器人下单 https://t.me/Lulaoshi_bot',
            '怎么进群': '👉 请使用机器人下单 https://t.me/Lulaoshi_bot',
            '求进群': '👉 请使用机器人下单 https://t.me/Lulaoshi_bot',
            '进群': '👉 请使用机器人下单 https://t.me/Lulaoshi_bot',
            '入群': '👉 请使用机器人下单 https://t.me/Lulaoshi_bot',
            '怎么入群': '👉 请使用机器人下单 https://t.me/Lulaoshi_bot',
        }
        self.auto_reply_enabled = True  # 是否启用智能回复
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理收到的消息"""
        try:
            message_text = update.message.text.strip() if update.message.text else ""
            chat_type = update.effective_chat.type
            chat_id = update.effective_chat.id
            user_name = update.effective_user.username or update.effective_user.first_name
            
            logger.info(f"收到消息: '{message_text}' 来自: {user_name} (Chat ID: {chat_id}, 类型: {chat_type})")
            
            admin_chat_id = Config.ADMIN_CHAT_ID
            is_admin_chat = admin_chat_id and str(chat_id) == str(admin_chat_id)

            # 处理私聊消息
            if chat_type == 'private':
                # 转发私信给管理员
                await self._forward_private_message_to_admin(update, context)

                if message_text == "27":
                    special_message = """小助理下单机器人： 👉https://t.me/Lulaoshi_bot

※平台是自助入群，机器人下单即可。

如果不太会使用平台，或者遇到任何问题，可以私信露老师：@mteacherlu。

除门槛相关露老师个人电报私信不接受闲聊，禁砍价，不强迫入门，也请保持基本礼貌，感谢理解。

注意事项：
1.露老师不做任何形式的线下服务！！！
2.因个人原因退群后不再重新拉群，还请注意一下。
3.支付过程中如有任何问题，可以私信管理员。

感谢大家的配合和支持！✨

---------------------------------------------------

相关群组与定制介绍：

日常群：稳定更新，露老师个人原创作品，会更新长视频以及多量照片，都是推特所看不到的内容。

女女群：稳定更新，除露老师外还可以看到另外几位女主，露老师与其他女主合作视频等。

第三视角群：不定期更新，每次活动拍摄由男友视角随心拍摄（还没入日常群和女女群的不推荐首次就购买第三视角群）。

定制视频：根据需求定制露老师视频，可SOLO、FM、FF、FFM、FMM，可按要求使用各种玩具和剧情设计。

※希望得到更详细介绍询问请私信"""

                    # 删除上一次的业务介绍消息
                    if self.last_business_intro_message_id:
                        try:
                            await context.bot.delete_message(
                                chat_id=self.chat_id,
                                message_id=self.last_business_intro_message_id
                            )
                            logger.info(f"🗑️ 已删除上一次的业务介绍消息 (消息ID: {self.last_business_intro_message_id})")
                        except Exception as e:
                            logger.warning(f"删除上一次业务介绍消息失败: {e}")

                    # 发送到配置的群组
                    sent_message = await context.bot.send_message(
                        chat_id=self.chat_id,
                        text=special_message,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )

                    # 保存新消息的ID
                    if sent_message:
                        self.last_business_intro_message_id = sent_message.message_id
                        logger.info(f"💾 已保存新业务介绍消息ID: {sent_message.message_id}")

                    # 给私聊用户发送确认消息
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="✅ 已向群组发送相关信息",
                        parse_mode='HTML'
                    )

                    logger.info(f"🎉 收到私聊触发词'27'，已向群组发送业务介绍消息 (来自用户: {user_name})")

                elif message_text.lower() == "clear":
                    if not is_admin_chat:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ 此命令仅管理员可用",
                            parse_mode='HTML'
                        )
                        logger.warning(f"未经授权的清除命令尝试 (来自用户: {user_name}, Chat ID: {chat_id})")
                        return
                    # 处理清除欢迎消息命令
                    await self._clear_welcome_messages(context)

                    # 给私聊用户发送确认消息
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="✅ 已清除群内所有欢迎消息",
                        parse_mode='HTML'
                    )

                    logger.info(f"🧹 收到私聊清除命令'clear'，已清除所有欢迎消息 (来自用户: {user_name})")

                elif message_text.lower() == "blacklist":
                    if not is_admin_chat:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ 此命令仅管理员可用",
                            parse_mode='HTML'
                        )
                        logger.warning(f"未经授权的黑名单查看尝试 (来自用户: {user_name}, Chat ID: {chat_id})")
                        return
                    # 处理查看黑名单命令
                    await self._show_blacklist(context, chat_id)
                    logger.info(f"📋 收到私聊黑名单查看命令 (来自用户: {user_name})")

                elif message_text.lower().startswith("unban "):
                    if not is_admin_chat:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ 此命令仅管理员可用",
                            parse_mode='HTML'
                        )
                        logger.warning(f"未经授权的解封尝试 (来自用户: {user_name}, Chat ID: {chat_id})")
                        return
                    # 处理从黑名单移除用户命令
                    try:
                        user_id_to_unban = int(message_text.split()[1])
                        await self._unban_user(context, chat_id, user_id_to_unban)
                        logger.info(f"🔓 收到私聊解封命令，用户ID: {user_id_to_unban} (来自用户: {user_name})")
                    except (IndexError, ValueError):
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ 命令格式错误，请使用: unban 用户ID",
                            parse_mode='HTML'
                        )

                elif message_text.lower() == "stats":
                    if not is_admin_chat:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ 此命令仅管理员可用",
                            parse_mode='HTML'
                        )
                        return
                    await self.handle_stats_command(chat_id, context)
                    logger.info(f"📊 收到统计查看命令 (来自用户: {user_name})")

                elif message_text.lower() == "logs":
                    if not is_admin_chat:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ 此命令仅管理员可用",
                            parse_mode='HTML'
                        )
                        return
                    await self.handle_logs_command(chat_id, context)
                    logger.info(f"📋 收到日志查看命令 (来自用户: {user_name})")

                elif message_text.lower() == "help":
                    await self.handle_help_command(chat_id, context, is_admin=is_admin_chat)
                    logger.info(f"❓ 收到帮助命令 (来自用户: {user_name})")

                elif message_text.lower() == "check":
                    if not is_admin_chat:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ 此命令仅管理员可用",
                            parse_mode='HTML'
                        )
                        return
                    await self.handle_check_command(chat_id, context)
                    logger.info(f"🔍 收到手动检查命令 (来自用户: {user_name})")

                elif message_text.lower().startswith("setinterval "):
                    if not is_admin_chat:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ 此命令仅管理员可用",
                            parse_mode='HTML'
                        )
                        return
                    interval_str = message_text.split()[1] if len(message_text.split()) > 1 else ""
                    await self.handle_setinterval_command(chat_id, context, interval_str)

                elif message_text.lower().startswith("toggle "):
                    if not is_admin_chat:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ 此命令仅管理员可用",
                            parse_mode='HTML'
                        )
                        return
                    feature = message_text.lower().split()[1] if len(message_text.split()) > 1 else ""
                    await self._toggle_feature(chat_id, context, feature)
                    logger.info(f"⏱️ 收到设置间隔命令 (来自用户: {user_name})")

                elif self._is_twitter_url(message_text):
                    # 处理私信发送的Twitter URL
                    if self.twitter_monitor:
                        logger.info(f"收到Twitter URL: {message_text}")

                        try:
                            # 从URL提取推文ID
                            tweet_id = self._extract_tweet_id(message_text)
                            if not tweet_id:
                                await context.bot.send_message(
                                    chat_id=chat_id,
                                    text="❌ 无法识别的Twitter URL格式",
                                    parse_mode='HTML'
                                )
                                return

                            # 获取推文详情
                            tweet_info = await run_in_thread(self.twitter_monitor.get_tweet_by_id, tweet_id)

                            if tweet_info:
                                # 发送到群组
                                tweet_text = tweet_info['text']
                                if tweet_text and len(tweet_text) > 800:
                                    tweet_text = tweet_text[:800] + "..."

                                tweet_message = f"""
🐦 <b>推文分享</b>

👤 <b>用户:</b> <a href=\"https://x.com/{tweet_info['username']}\">{tweet_info['username']}</a>
📝 <b>内容:</b> {self._escape_html(tweet_text)}
🕒 <b>时间:</b> {tweet_info['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}
"""

                                tweet_message += f"\n\n🔗 <a href=\"{tweet_info['url']}\">查看原推文</a>".strip()

                                preview_url = tweet_info.get('preview_image_url')
                                if preview_url:
                                    if len(tweet_message) > 900:
                                        tweet_message = tweet_message[:900] + "..."

                                    await context.bot.send_photo(
                                        chat_id=self.chat_id,
                                        photo=preview_url,
                                        caption=tweet_message,
                                        parse_mode='HTML'
                                    )
                                else:
                                    await context.bot.send_message(
                                        chat_id=self.chat_id,
                                        text=tweet_message,
                                        parse_mode='HTML',
                                        disable_web_page_preview=False
                                    )

                                # 给私聊用户发送确认消息
                                await context.bot.send_message(
                                    chat_id=chat_id,
                                    text="✅ 已向群组分享该推文",
                                    parse_mode='HTML'
                                )

                                logger.info(f"🎉 成功分享推文到群组 (推文ID: {tweet_id}, 来自用户: {user_name})")
                            else:
                                # 无法获取推文
                                await context.bot.send_message(
                                    chat_id=chat_id,
                                    text="❌ 无法获取该推文，可能是私密推文或推文不存在",
                                    parse_mode='HTML'
                                )

                        except Exception as e:
                            logger.error(f"处理Twitter URL失败: {e}")

                            # 根据错误类型提供不同的提示
                            if "429" in str(e) or "rate limit" in str(e).lower():
                                error_msg = "❌ Twitter API速率限制，请等待15分钟后重试"
                            elif "timeout" in str(e).lower() or "connection" in str(e).lower():
                                error_msg = "❌ 网络连接超时，请稍后再试"
                            elif "unauthorized" in str(e).lower() or "401" in str(e):
                                error_msg = "❌ Twitter API认证失败，请联系管理员"
                            elif "not found" in str(e).lower() or "404" in str(e):
                                error_msg = "❌ 推文不存在或已被删除"
                            else:
                                error_msg = f"❌ 处理推文失败: {str(e)[:50]}"

                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=error_msg,
                                parse_mode='HTML'
                            )
                    else:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ Twitter服务未初始化",
                            parse_mode='HTML'
                        )

                else:
                    # 对其他私聊消息给予提示
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="👋 你好！\n\n💡 可用功能：\n• 发送 '27' - 向群组发送业务介绍\n• 发送 'clear' - 清除群内所有欢迎消息\n• 发送 'blacklist' - 查看黑名单\n• 发送 'unban 用户ID' - 从黑名单移除用户\n• 发送 Twitter URL - 分享推文到群组\n\n📝 支持的URL格式：\n• https://twitter.com/用户名/status/推文ID\n• https://x.com/用户名/status/推文ID",
                        parse_mode='HTML'
                    )
                    logger.info(f"收到私聊消息'{message_text}'，已回复提示信息 (来自用户: {user_name})")
            # 处理群组消息
            elif str(chat_id) == str(self.chat_id):
                user_id = update.effective_user.id
                
                # 检查是否是待验证用户的验证消息
                if self.verification_enabled and str(user_id) in self.pending_verifications:
                    await self._handle_verification(update, context, user_id, message_text)
                    return
                
                # 广告检测
                if self.ad_detection_enabled:
                    is_ad, matched_keyword = self._detect_ad(message_text)
                    if is_ad:
                        await self._handle_ad_message(update, context, user_id, user_name, matched_keyword)
                        return
                
                # 智能回复
                if self.auto_reply_enabled:
                    reply = self._get_auto_reply(message_text)
                    if reply:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=reply,
                            parse_mode='HTML',
                            reply_to_message_id=update.message.message_id
                        )
                        self._log_activity('auto_reply', f"触发词: {message_text[:20]}")
                        return
                
                logger.info(f"收到群组消息: '{message_text}' 来自: {user_name}")
            else:
                # 忽略其他群组的消息
                logger.info(f"忽略来自其他群组的消息: {chat_id}")

        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")

    async def _show_blacklist(self, context, chat_id):
        """显示黑名单列表"""
        try:
            blacklist = self.database.get_blacklist()
            blacklist_count = len(blacklist)

            if blacklist_count == 0:
                message = "📋 <b>黑名单管理</b>\n\n✅ 黑名单为空，暂无被封禁用户。"
            else:
                message = f"📋 <b>黑名单管理</b>\n\n👥 <b>总计:</b> {blacklist_count} 个用户\n\n"
                
                for i, (user_id, user_name, username, reason, leave_count, added_at) in enumerate(blacklist, 1):
                    # 格式化时间
                    try:
                        from datetime import datetime
                        if isinstance(added_at, str):
                            added_time = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
                        else:
                            added_time = added_at
                        time_str = added_time.strftime('%Y-%m-%d %H:%M')
                    except:
                        time_str = str(added_at)[:16]

                    message += f"""<b>{i}.</b> {self._escape_html(user_name or '未知用户')}
• ID: <code>{user_id}</code>
• 用户名: @{username or '无'}
• 原因: {reason}
• 离群次数: {leave_count}
• 加入时间: {time_str}

"""

                message += f"\n💡 <b>管理提示:</b>\n• 发送 'unban 用户ID' 可移除用户\n• 例如: unban {blacklist[0][0]}"

            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML'
            )

        except Exception as e:
            logger.error(f"显示黑名单失败: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ 获取黑名单信息失败",
                parse_mode='HTML'
            )

    async def _unban_user(self, context, chat_id, user_id):
        """从黑名单移除用户"""
        try:
            # 检查用户是否在黑名单中
            if not self.database.is_user_blacklisted(user_id):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ 用户 ID {user_id} 不在黑名单中",
                    parse_mode='HTML'
                )
                return

            # 从黑名单移除
            success = self.database.remove_from_blacklist(user_id)
            
            if success:
                # 获取用户信息（如果在活动管理器中）
                user_info = ""
                user_data = self.user_activity_manager.get(str(user_id))
                if user_data:
                    user_info = f" ({user_data['user_name']})"

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ 已将用户 ID {user_id}{user_info} 从黑名单中移除",
                    parse_mode='HTML'
                )

                # 通知管理员
                admin_chat_id = Config.ADMIN_CHAT_ID
                if admin_chat_id and str(chat_id) != str(admin_chat_id):
                    await context.bot.send_message(
                        chat_id=admin_chat_id,
                        text=f"🔓 <b>用户解封通知</b>\n\n用户 ID {user_id}{user_info} 已从黑名单中移除。",
                        parse_mode='HTML'
                    )

                logger.info(f"🔓 用户 ID {user_id} 已从黑名单中移除")
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ 移除用户 ID {user_id} 失败",
                    parse_mode='HTML'
                )

        except Exception as e:
            logger.error(f"移除黑名单用户失败: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ 操作失败，请稍后重试",
                parse_mode='HTML'
            )

    async def _forward_private_message_to_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """转发私信消息给管理员"""
        try:
            admin_chat_id = Config.ADMIN_CHAT_ID
            if not admin_chat_id:
                logger.warning("ADMIN_CHAT_ID 未配置，无法转发私信")
                return

            user = update.effective_user
            message = update.message
            chat_id = update.effective_chat.id

            # 检查是否是管理员自己发送的消息，如果是则不转发
            if str(chat_id) == str(admin_chat_id):
                logger.info(f"收到管理员消息，不进行转发: {message.text[:50] if message.text else '非文本消息'}...")
                return

            # 获取用户信息
            user_name = user.first_name or user.username or f"用户{user.id}"
            username = user.username or "无用户名"
            user_id = user.id

            # 获取消息内容
            message_text = message.text or ""
            message_time = message.date.strftime('%Y-%m-%d %H:%M:%S UTC')

            # 构建转发消息
            forward_message = f"""📨 <b>收到私信</b>

👤 <b>用户信息:</b>
• 姓名: {self._escape_html(user_name)}
• 用户名: @{username}
• 用户ID: {user_id}
• Chat ID: {chat_id}

📝 <b>消息内容:</b>
{self._escape_html(message_text)}

🕒 <b>发送时间:</b> {message_time}

💬 <b>回复方式:</b> 可直接回复此消息或使用 Chat ID: {chat_id}"""

            # 发送转发消息给管理员
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=forward_message,
                parse_mode='HTML'
            )

            logger.info(f"📨 已转发私信给管理员: {user_name} (ID: {user_id}) - {message_text[:50]}...")

        except Exception as e:
            logger.error(f"转发私信给管理员失败: {e}")

    async def _clear_welcome_messages(self, context: ContextTypes.DEFAULT_TYPE):
        """清除所有欢迎消息"""
        try:
            cleared_count = 0
            failed_count = 0

            # 复制列表以避免在迭代时修改
            messages_to_clear = self.welcome_messages.copy()

            for message_info in messages_to_clear:
                try:
                    await context.bot.delete_message(
                        chat_id=message_info['chat_id'],
                        message_id=message_info['message_id']
                    )
                    cleared_count += 1
                    logger.info(f"🗑️ 已删除欢迎消息 (消息ID: {message_info['message_id']}, 用户: {message_info['user_name']})")
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"删除欢迎消息失败 (消息ID: {message_info['message_id']}): {e}")

            # 清空欢迎消息列表
            self.welcome_messages.clear()

            # 发送清除结果给管理员
            admin_chat_id = Config.ADMIN_CHAT_ID
            if admin_chat_id:
                result_message = f"""🧹 <b>欢迎消息清除完成</b>

📊 <b>清除统计:</b>
• 成功删除: {cleared_count} 条
• 删除失败: {failed_count} 条
• 总计处理: {len(messages_to_clear)} 条

⏰ <b>清除时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 所有欢迎消息已清除"""

                await context.bot.send_message(
                    chat_id=admin_chat_id,
                    text=result_message,
                    parse_mode='HTML'
                )

            logger.info(f"🧹 欢迎消息清除完成: 成功 {cleared_count} 条, 失败 {failed_count} 条")

        except Exception as e:
            logger.error(f"清除欢迎消息时发生错误: {e}")

    async def handle_chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理群组成员变化"""
        try:
            chat_member_update = update.chat_member
            chat_id = chat_member_update.chat.id

            # 只处理目标群组的成员变化
            if str(chat_id) != str(self.chat_id):
                return

            old_status = chat_member_update.old_chat_member.status
            new_status = chat_member_update.new_chat_member.status
            user = chat_member_update.new_chat_member.user
            user_id = user.id
            user_name = user.first_name or user.username or f"用户{user_id}"
            username = user.username or "无用户名"
            current_time = datetime.now()

            # 记录用户活动 - 使用内存管理器
            user_data = self.user_activity_manager.get(str(user_id))
            if not user_data:
                user_data = {
                    'user_name': user_name,
                    'username': username,
                    'join_times': [],
                    'leave_times': [],
                    'total_joins': 0,
                    'total_leaves': 0
                }
                self.user_activity_manager.add(str(user_id), user_data)

            # 更新用户信息（可能会变化）
            user_data['user_name'] = user_name
            user_data['username'] = username

            # 检查用户加入
            if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator', 'creator']:
                # 记录加入时间
                user_data['join_times'].append(current_time)
                user_data['total_joins'] += 1

                logger.info(f"👋 用户加入: {user_name} (ID: {user_id}, 用户名: @{username})")
                self.stats['users_joined'] += 1
                self._log_activity('user_joined', f"{user_name} (ID: {user_id})")

                # 检查是否是重复进群用户（超过1次才通知）
                if user_data['total_joins'] > 1:
                    await self._notify_repeat_user(user_id, 'join', context)

                # 发送欢迎消息
                welcome_message = f"""🎉 欢迎 <b>{self._escape_html(user_name)}</b> 加入露老师聊天群！

🔍 认准露老师唯一账号：
• X账号：<a href="https://x.com/xiuchiluchu910"><b>xiuchiluchu910</b></a>
• Telegram账号：<a href="https://t.me/mteacherlu"><b>@mteacherlu</b></a>

💬 群内随意聊天，但请勿轻易相信任何陌生人，谨防诈骗 ⚠️

📌 <b>重要提示：</b>如果您进群后不显示内容，请尝试以下解决办法：
1. Google搜索相关问题，例如在 <a href="https://www.google.com">Google</a> 中搜索：<b>telegram进群后不显示内容</b>
2. 参考解决方案网页：<a href="https://blog.sinovale.com/2912.html">https://blog.sinovale.com/2912.html</a>
3. 重启Telegram应用或清除缓存
4. 检查网络连接是否稳定"""

                sent_message = await context.bot.send_message(
                    chat_id=self.chat_id,
                    text=welcome_message,
                    parse_mode='HTML'
                )
                self.stats['welcome_sent'] += 1

                # 自动私信新用户解锁敏感内容说明
                await self._send_new_user_guide(context, user_id, user_name)

                if self.verification_enabled and new_status == 'member':
                    await self._send_verification_challenge(context, user_id, user_name)

                # 记录欢迎消息信息
                if sent_message:
                    welcome_info = {
                        'message_id': sent_message.message_id,
                        'chat_id': self.chat_id,
                        'user_name': user_name,
                        'user_id': user_id,
                        'timestamp': current_time
                    }
                    self.welcome_messages.append(welcome_info)
                    logger.info(f"📝 已记录欢迎消息: {user_name} (消息ID: {sent_message.message_id})")

                # 安排1分钟后删除消息（根据用户需求）
                if sent_message:
                    try:
                        if context.job_queue:
                            context.job_queue.run_once(
                                self._delete_welcome_message,
                                when=60,  # 1分钟 = 60秒
                                data={
                                    'chat_id': self.chat_id,
                                    'message_id': sent_message.message_id,
                                    'user_name': user_name
                                }
                            )
                            logger.info(f"⏰ 已安排1分钟后删除欢迎消息 (消息ID: {sent_message.message_id})")
                        else:
                            logger.warning("JobQueue不可用，无法安排自动删除欢迎消息")
                    except Exception as e:
                        logger.error(f"安排删除欢迎消息失败: {e}")

            # 检查用户离开
            elif old_status in ['member', 'administrator', 'creator'] and new_status in ['left', 'kicked']:
                # 记录离开时间
                user_data['leave_times'].append(current_time)
                user_data['total_leaves'] += 1

                logger.info(f"👋 用户离开: {user_name} (ID: {user_id}, 用户名: @{username})")
                self.stats['users_left'] += 1
                self._log_activity('user_left', f"{user_name} (ID: {user_id})")

                # 检查是否是第二次离开，如果是则加入黑名单
                if user_data['total_leaves'] >= 2:
                    # 添加到黑名单（移除黑名单检查，确保每次第二次离开都加入）
                    success = self.database.add_to_blacklist(
                        user_id=user_id,
                        user_name=user_name,
                        username=username,
                        leave_count=user_data['total_leaves'],
                        reason=f"多次离群 ({user_data['total_leaves']}次)"
                    )
                    
                    if success:
                        # 通知管理员用户已被加入黑名单
                        await self._notify_user_blacklisted(user_id, context)
                        logger.info(f"🚫 用户 {user_name} (ID: {user_id}) 因多次离群已自动加入黑名单")

                # 如果用户离开超过1次，通知管理员
                if user_data['total_leaves'] > 1:
                    await self._notify_repeat_user(user_id, 'leave', context)

        except Exception as e:
            logger.error(f"处理群组成员变化时发生错误: {e}")

    async def _notify_repeat_user(self, user_id, action, context):
        """通知管理员用户的重复进群/退群行为"""
        try:
            user_data = self.user_activity_manager.get(str(user_id))
            if not user_data:
                logger.warning(f"未找到用户活动数据: {user_id}")
                return
                
            user_name = user_data['user_name']
            username = user_data['username']

            # 构建活动历史
            activity_history = []

            # 合并加入和离开时间，按时间排序
            all_activities = []
            for join_time in user_data['join_times']:
                all_activities.append(('加入', join_time))
            for leave_time in user_data['leave_times']:
                all_activities.append(('离开', leave_time))

            # 按时间排序
            all_activities.sort(key=lambda x: x[1])

            # 格式化活动历史
            for activity_type, activity_time in all_activities:
                time_str = activity_time.strftime('%Y-%m-%d %H:%M:%S')
                activity_history.append(f"• {activity_type}: {time_str}")

            # 构建通知消息
            action_text = "加入" if action == 'join' else "离开"
            notification_message = f"""🚨 <b>用户活动监控</b>

👤 <b>用户信息:</b>
• 姓名: {self._escape_html(user_name)}
• 用户名: @{username}
• ID: {user_id}

📊 <b>活动统计:</b>
• 总加入次数: {user_data['total_joins']}
• 总离开次数: {user_data['total_leaves']}
• 当前动作: {action_text}

📝 <b>活动历史:</b>
{chr(10).join(activity_history)}

⚠️ 该用户存在多次进群/退群行为，请注意关注。"""

            # 发送私信给管理员
            try:
                admin_chat_id = Config.ADMIN_CHAT_ID
                if admin_chat_id:
                    await context.bot.send_message(
                        chat_id=admin_chat_id,
                        text=notification_message,
                        parse_mode='HTML'
                    )
                    logger.info(f"📨 已向管理员发送用户活动通知: {user_name} ({action_text})")
                else:
                    logger.warning("ADMIN_CHAT_ID 未配置，无法发送通知")
                    logger.info(f"用户活动详情 - {user_name} (ID: {user_id}, @{username}) {action_text}")
            except Exception as e:
                logger.error(f"向管理员发送通知失败: {e}")
                # 如果发送失败，记录详细信息到日志
                logger.info(f"用户活动详情 - {user_name} (ID: {user_id}, @{username}) {action_text}")

        except Exception as e:
            logger.error(f"处理用户活动通知时发生错误: {e}")

    async def _notify_user_blacklisted(self, user_id, context):
        """通知管理员用户已被加入黑名单"""
        try:
            user_data = self.user_activity_manager.get(str(user_id))
            if not user_data:
                logger.warning(f"未找到用户活动数据: {user_id}")
                return
                
            user_name = user_data['user_name']
            username = user_data['username']

            # 构建活动历史
            activity_history = []
            all_activities = []
            for join_time in user_data['join_times']:
                all_activities.append(('加入', join_time))
            for leave_time in user_data['leave_times']:
                all_activities.append(('离开', leave_time))

            # 按时间排序
            all_activities.sort(key=lambda x: x[1])

            # 格式化活动历史
            for activity_type, activity_time in all_activities:
                time_str = activity_time.strftime('%Y-%m-%d %H:%M:%S')
                activity_history.append(f"• {activity_type}: {time_str}")

            blacklist_message = f"""🚫 <b>用户已自动加入黑名单</b>

👤 <b>用户信息:</b>
• 姓名: {self._escape_html(user_name)}
• 用户名: @{username}
• ID: {user_id}

📊 <b>统计信息:</b>
• 总加入次数: {user_data['total_joins']}
• 总离开次数: {user_data['total_leaves']}
• 加入黑名单原因: 多次离群 ({user_data['total_leaves']}次)

📝 <b>活动历史:</b>
{chr(10).join(activity_history)}

⚠️ 该用户因多次离群已被自动加入黑名单。

💡 <b>管理命令:</b>
• 发送 'blacklist' - 查看黑名单
• 发送 'unban {user_id}' - 从黑名单移除用户"""

            # 发送私信给管理员
            try:
                admin_chat_id = Config.ADMIN_CHAT_ID
                if admin_chat_id:
                    await context.bot.send_message(
                        chat_id=admin_chat_id,
                        text=blacklist_message,
                        parse_mode='HTML'
                    )
                    logger.info(f"📨 已向管理员发送黑名单通知: {user_name}")
                else:
                    logger.warning("ADMIN_CHAT_ID 未配置，无法发送黑名单通知")
            except Exception as e:
                logger.error(f"向管理员发送黑名单通知失败: {e}")

        except Exception as e:
            logger.error(f"处理黑名单通知时发生错误: {e}")

    def _detect_ad(self, text: str) -> tuple:
        """检测消息是否为广告
        Returns: (is_ad: bool, matched_keyword: str)
        """
        if not text:
            return False, ""
        
        text_lower = text.lower()
        
        # 检查广告关键词
        for keyword in self.ad_keywords:
            if keyword.lower() in text_lower:
                # 排除白名单（群主相关链接）
                whitelist = ['t.me/lulaoshi_bot', 't.me/mteacherlu', '@mteacherlu', 'x.com/xiuchiluchu910']
                is_whitelisted = any(w in text_lower for w in whitelist)
                if not is_whitelisted:
                    return True, keyword
        
        return False, ""

    def _get_auto_reply(self, text: str) -> str:
        """获取智能回复内容"""
        if not text:
            return ""
        
        text_lower = text.lower()
        for keyword, reply in self.auto_replies.items():
            if keyword in text_lower:
                return reply
        
        return ""

    async def _handle_ad_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  user_id: int, user_name: str, matched_keyword: str):
        """处理广告消息"""
        try:
            message_id = update.message.message_id
            
            # 删除广告消息
            try:
                await context.bot.delete_message(
                    chat_id=self.chat_id,
                    message_id=message_id
                )
                logger.info(f"🗑️ 已删除疑似广告消息 (用户: {user_name}, 关键词: {matched_keyword})")
            except Exception as e:
                logger.warning(f"删除广告消息失败: {e}")
            
            # 记录日志
            self._log_activity('ad_deleted', f"用户: {user_name}, 关键词: {matched_keyword}")
            self.stats['commands_processed'] += 1
            
            # 通知管理员
            admin_chat_id = Config.ADMIN_CHAT_ID
            if admin_chat_id:
                ad_notice = f"""⚠️ <b>广告检测警报</b>

👤 <b>用户:</b> {utils.escape_html(user_name)}
🆔 <b>用户ID:</b> <code>{user_id}</code>
🔍 <b>触发词:</b> {utils.escape_html(matched_keyword)}
📝 <b>消息内容:</b>
{utils.escape_html(update.message.text[:200])}...

✅ 消息已自动删除"""
                
                await context.bot.send_message(
                    chat_id=admin_chat_id,
                    text=ad_notice,
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"处理广告消息失败: {e}")

    async def _handle_verification(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    user_id: int, message_text: str):
        """处理入群验证"""
        try:
            verification = self.pending_verifications.get(str(user_id))
            if not verification:
                return
            
            # 检查是否超时
            if datetime.now() > verification['expires']:
                del self.pending_verifications[str(user_id)]
                # 踢出超时用户
                try:
                    await context.bot.ban_chat_member(
                        chat_id=self.chat_id,
                        user_id=user_id
                    )
                    await context.bot.unban_chat_member(
                        chat_id=self.chat_id,
                        user_id=user_id
                    )
                    logger.info(f"⏰ 用户 {user_id} 验证超时，已移除")
                except Exception as e:
                    logger.error(f"移除超时用户失败: {e}")
                return
            
            # 检查验证码
            if message_text.strip() == verification['code']:
                # 验证成功
                del self.pending_verifications[str(user_id)]

                # 恢复用户发言权限（恢复为群默认权限）
                try:
                    chat = await context.bot.get_chat(self.chat_id)
                    permissions = chat.permissions or ChatPermissions.all_permissions()
                    await context.bot.restrict_chat_member(
                        chat_id=self.chat_id,
                        user_id=user_id,
                        permissions=permissions
                    )
                except Exception as e:
                    logger.warning(f"恢复用户发言权限失败: {e}")
                
                # 删除验证消息
                try:
                    await context.bot.delete_message(
                        chat_id=self.chat_id,
                        message_id=update.message.message_id
                    )
                except:
                    pass
                
                await context.bot.send_message(
                    chat_id=self.chat_id,
                    text=f"✅ <b>{utils.escape_html(update.effective_user.first_name)}</b> 验证成功，欢迎加入！",
                    parse_mode='HTML'
                )
                self._log_activity('verification_passed', f"用户ID: {user_id}")
                logger.info(f"✅ 用户 {user_id} 验证成功")
            else:
                # 验证失败，删除错误消息
                try:
                    await context.bot.delete_message(
                        chat_id=self.chat_id,
                        message_id=update.message.message_id
                    )
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"处理验证失败: {e}")

    async def _send_verification_challenge(self, context: ContextTypes.DEFAULT_TYPE, 
                                            user_id: int, user_name: str):
        """发送入群验证挑战"""
        # 生成简单的数学验证码
        a, b = random.randint(1, 10), random.randint(1, 10)
        code = str(a + b)
        
        # 记录待验证信息
        self.pending_verifications[str(user_id)] = {
            'code': code,
            'expires': datetime.now() + timedelta(seconds=self.verification_timeout)
        }

        try:
            restricted_permissions = ChatPermissions(
                can_send_messages=True,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_manage_topics=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
            )
            await context.bot.restrict_chat_member(
                chat_id=self.chat_id,
                user_id=user_id,
                permissions=restricted_permissions,
                until_date=self.pending_verifications[str(user_id)]['expires']
            )
        except Exception as e:
            logger.warning(f"限制新用户发言权限失败: {e}")
        
        verification_message = f"""🔐 <b>入群验证</b>

👋 你好 <b>{utils.escape_html(user_name)}</b>！

请在 {self.verification_timeout // 60} 分钟内回答以下问题完成验证：

❓ <b>{a} + {b} = ?</b>

⚠️ 超时未验证将被自动移出群组"""

        sent = await context.bot.send_message(
            chat_id=self.chat_id,
            text=verification_message,
            parse_mode='HTML'
        )
        
        # 安排超时检查
        if self.application.job_queue:
            self.application.job_queue.run_once(
                self._check_verification_timeout,
                when=self.verification_timeout,
                data={'user_id': user_id, 'message_id': sent.message_id}
            )

    async def _check_verification_timeout(self, context: ContextTypes.DEFAULT_TYPE):
        """检查验证是否超时"""
        try:
            job_data = context.job.data
            user_id = job_data['user_id']
            message_id = job_data['message_id']
            
            # 如果用户还在待验证列表中，说明超时了
            if str(user_id) in self.pending_verifications:
                del self.pending_verifications[str(user_id)]
                
                # 删除验证消息
                try:
                    await context.bot.delete_message(
                        chat_id=self.chat_id,
                        message_id=message_id
                    )
                except:
                    pass
                
                # 踢出用户
                try:
                    await context.bot.ban_chat_member(
                        chat_id=self.chat_id,
                        user_id=user_id
                    )
                    await context.bot.unban_chat_member(
                        chat_id=self.chat_id,
                        user_id=user_id
                    )
                    logger.info(f"⏰ 用户 {user_id} 验证超时，已移除")
                    self._log_activity('verification_timeout', f"用户ID: {user_id}")
                except Exception as e:
                    logger.error(f"移除超时用户失败: {e}")
                    
        except Exception as e:
            logger.error(f"检查验证超时失败: {e}")

    async def _send_new_user_guide(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, user_name: str):
        """自动私信新用户解锁敏感内容说明"""
        try:
            guide_message = f"""👋 <b>你好 {utils.escape_html(user_name)}！欢迎加入露老师聊天群！</b>

⚠️ <b>重要提示：</b>如果您进群后看不到群内容（因为是敏感内容），请按以下步骤解锁：

📱 <b>解锁步骤：</b>
1️⃣ 用浏览器打开 Telegram 网页版：
👉 <a href="https://web.telegram.org/">https://web.telegram.org/</a>

2️⃣ 登录后点击左上角的 <b>Settings</b>（设置）

3️⃣ 找到 <b>"Show Sensitive Content"</b> 选项并打勾 ✅

4️⃣ 退出登录（包括手机App）

5️⃣ 重新登录，重新加群即可解封！

━━━━━━━━━━━━━━━━━━━━

🛒 <b>下单购买请使用小助理机器人：</b>
👉 <a href="https://t.me/Lulaoshi_bot">https://t.me/Lulaoshi_bot</a>

━━━━━━━━━━━━━━━━━━━━

🔍 <b>认准露老师唯一账号：</b>
• X账号：<a href="https://x.com/xiuchiluchu910"><b>@xiuchiluchu910</b></a>
• Telegram账号：<a href="https://t.me/mteacherlu"><b>@mteacherlu</b></a>

⚠️ 请勿轻易相信任何陌生人，谨防诈骗！"""

            await context.bot.send_message(
                chat_id=user_id,
                text=guide_message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            logger.info(f"📨 已向新用户 {user_name} (ID: {user_id}) 发送入群指南私信")
            self._log_activity('guide_sent', f"用户: {user_name} (ID: {user_id})")
            
        except Exception as e:
            # 用户可能禁止了机器人私信，记录但不报错
            if "bot can't initiate" in str(e).lower() or "forbidden" in str(e).lower():
                logger.warning(f"⚠️ 无法向用户 {user_name} (ID: {user_id}) 发送私信 - 用户可能未启动机器人")
            else:
                logger.error(f"发送新用户指南私信失败: {e}")

    async def _delete_welcome_message(self, context: ContextTypes.DEFAULT_TYPE):
        """删除欢迎消息的回调函数"""
        try:
            job_data = context.job.data
            chat_id = job_data['chat_id']
            message_id = job_data['message_id']
            user_name = job_data['user_name']

            # 删除消息
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )

            # 从欢迎消息列表中移除
            self.welcome_messages = [
                msg for msg in self.welcome_messages
                if msg['message_id'] != message_id
            ]

            logger.info(f"🗑️ 已删除用户 {user_name} 的欢迎消息 (消息ID: {message_id})")

        except Exception as e:
            # 如果删除失败（比如消息已被手动删除），记录但不报错
            logger.warning(f"删除欢迎消息失败: {e}")
            if "message to delete not found" not in str(e).lower():
                logger.error(f"删除欢迎消息时发生意外错误: {e}")

            # 即使删除失败，也从列表中移除（可能消息已被手动删除）
            job_data = context.job.data
            message_id = job_data['message_id']
            self.welcome_messages = [
                msg for msg in self.welcome_messages
                if msg['message_id'] != message_id
            ]

    def _escape_html(self, text):
        """转义HTML特殊字符 - 已弃用，请直接使用utils.escape_html()"""
        # 为了向后兼容，调用utils模块的函数
        import warnings
        warnings.warn("_escape_html方法已弃用，请使用utils.escape_html()", DeprecationWarning, stacklevel=2)
        return utils.escape_html(text)

    def _is_twitter_url(self, text):
        """检查文本是否包含Twitter URL - 使用utils模块"""
        return utils.is_twitter_url(text)

    def _extract_tweet_id(self, url):
        """从Twitter URL中提取推文ID - 使用utils模块"""
        return utils.extract_tweet_id(url)
    


    def _log_activity(self, action: str, details: str = ""):
        """记录操作日志"""
        log_entry = {
            'time': datetime.now(),
            'action': action,
            'details': details
        }
        self.activity_logs.append(log_entry)
        # 只保留最近100条日志
        if len(self.activity_logs) > 100:
            self.activity_logs = self.activity_logs[-100:]

    async def check_twitter_updates(self):
        """检查Twitter新推文并自动发送到群组"""
        try:
            now = datetime.now()
            
            # 检查是否到了检查时间
            if self.last_twitter_check_time:
                elapsed = (now - self.last_twitter_check_time).total_seconds()
                if elapsed < self.twitter_check_interval:
                    return  # 还没到检查时间
            
            # 更新检查时间
            self.last_twitter_check_time = now
            
            if not self.twitter_monitor:
                logger.warning("Twitter监控未初始化")
                return

            if not self.twitter_auto_forward_enabled:
                return
            
            username = Config.TWITTER_USERNAME
            logger.info(f"🔍 检查 @{username} 的新推文...")
            
            # 获取新推文
            new_tweets = await run_in_thread(self.twitter_monitor.check_new_tweets, username)
            
            if new_tweets:
                logger.info(f"📢 发现 {len(new_tweets)} 条新推文")
                
                for tweet in new_tweets:
                    try:
                        tweet_text = tweet.get('text', '')
                        if tweet_text and len(tweet_text) > 800:
                            tweet_text = tweet_text[:800] + "..."

                        # 构建推文消息
                        tweet_message = f"""🐦 <b><a href=\"https://x.com/{username}\">{username}</a> 发布了新推文</b>

📝 <b>内容:</b>
{utils.escape_html(tweet_text)}

🕒 <b>时间:</b> {tweet['created_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(tweet['created_at'], 'strftime') else tweet['created_at']}

🔗 <a href="{tweet['url']}">查看原推文</a>"""

                        # 发送到群组
                        preview_url = tweet.get('preview_image_url')
                        if preview_url:
                            if len(tweet_message) > 900:
                                tweet_message = tweet_message[:900] + "..."

                            await self.application.bot.send_photo(
                                chat_id=self.chat_id,
                                photo=preview_url,
                                caption=tweet_message,
                                parse_mode='HTML'
                            )
                        else:
                            await self.application.bot.send_message(
                                chat_id=self.chat_id,
                                text=tweet_message,
                                parse_mode='HTML',
                                disable_web_page_preview=False
                            )
                        
                        self.stats['tweets_sent'] += 1
                        self._log_activity('tweet_sent', f"推文ID: {tweet['id']}")
                        logger.info(f"✅ 已发送推文到群组: {tweet['id']}")
                        
                        # 避免发送过快
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"发送推文失败: {e}")
                        self.stats['errors'] += 1
            else:
                logger.info(f"📭 @{username} 暂无新推文")
                
        except Exception as e:
            logger.error(f"检查Twitter更新失败: {e}")
            self.stats['errors'] += 1

    async def _toggle_feature(self, chat_id, context, feature: str):
        """切换功能开关"""
        try:
            feature_map = {
                'verification': ('verification_enabled', '入群验证'),
                'verify': ('verification_enabled', '入群验证'),
                'ad': ('ad_detection_enabled', '广告检测'),
                'ads': ('ad_detection_enabled', '广告检测'),
                'reply': ('auto_reply_enabled', '智能回复'),
                'autoreply': ('auto_reply_enabled', '智能回复'),
                'twitter': ('twitter_auto_forward_enabled', '推文自动转发'),
                'tweets': ('twitter_auto_forward_enabled', '推文自动转发'),
            }
            
            if feature not in feature_map:
                features_list = "\n".join([f"• <code>{k}</code> - {v[1]}" for k, v in feature_map.items()])
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ 未知功能: {feature}\n\n可用功能:\n{features_list}",
                    parse_mode='HTML'
                )
                return
            
            attr_name, display_name = feature_map[feature]
            current_value = getattr(self, attr_name)
            new_value = not current_value
            setattr(self, attr_name, new_value)
            
            status = "✅ 已开启" if new_value else "❌ 已关闭"
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔧 <b>{display_name}</b> {status}",
                parse_mode='HTML'
            )
            
            self._log_activity('feature_toggled', f"{display_name}: {new_value}")
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"切换功能失败: {e}")
            self.stats['errors'] += 1

    async def handle_stats_command(self, chat_id, context):
        """处理统计命令"""
        try:
            uptime = datetime.now() - self.stats['start_time']
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # 获取数据库统计
            processed_tweets = self.database.get_processed_tweets_count() if self.database else 0
            blacklist_count = self.database.get_blacklist_count() if self.database else 0
            
            stats_message = f"""📊 <b>TeleLuX 运行统计</b>

⏱️ <b>运行时长:</b> {days}天 {hours}小时 {minutes}分钟

📈 <b>本次运行统计:</b>
• 发送推文: {self.stats['tweets_sent']} 条
• 欢迎消息: {self.stats['welcome_sent']} 条
• 用户加入: {self.stats['users_joined']} 人
• 用户离开: {self.stats['users_left']} 人
• 命令处理: {self.stats['commands_processed']} 次
• 错误次数: {self.stats['errors']} 次

💾 <b>数据库统计:</b>
• 已处理推文: {processed_tweets} 条
• 黑名单用户: {blacklist_count} 人

🔧 <b>系统配置:</b>
• 监控用户: @{Config.TWITTER_USERNAME}
• 检查间隔: {self.twitter_check_interval} 秒
• 启动时间: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}"""

            await context.bot.send_message(
                chat_id=chat_id,
                text=stats_message,
                parse_mode='HTML'
            )
            self.stats['commands_processed'] += 1
            self._log_activity('stats_viewed', f"Chat ID: {chat_id}")
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            self.stats['errors'] += 1

    async def handle_logs_command(self, chat_id, context, count=10):
        """处理日志查询命令"""
        try:
            if not self.activity_logs:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="📋 暂无操作日志记录",
                    parse_mode='HTML'
                )
                return
            
            # 获取最近的日志
            recent_logs = self.activity_logs[-count:]
            recent_logs.reverse()  # 最新的在前
            
            logs_text = "📋 <b>最近操作日志</b>\n\n"
            for i, log in enumerate(recent_logs, 1):
                time_str = log['time'].strftime('%m-%d %H:%M:%S')
                logs_text += f"{i}. [{time_str}] <b>{log['action']}</b>\n"
                if log['details']:
                    logs_text += f"   {log['details']}\n"
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=logs_text,
                parse_mode='HTML'
            )
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"获取日志失败: {e}")
            self.stats['errors'] += 1

    async def handle_help_command(self, chat_id, context, is_admin=False):
        """处理帮助命令"""
        try:
            help_message = """📖 <b>TeleLuX 命令帮助</b>

💡 <b>基础命令:</b>
• <code>27</code> - 发送业务介绍到群组
• <code>help</code> - 显示此帮助信息
• 发送 Twitter URL - 分享推文到群组"""

            if is_admin:
                help_message += """

🔐 <b>管理员命令:</b>
• <code>stats</code> - 查看运行统计
• <code>logs</code> - 查看最近操作日志
• <code>clear</code> - 清除所有欢迎消息
• <code>blacklist</code> - 查看黑名单
• <code>unban 用户ID</code> - 解除用户封禁
• <code>check</code> - 立即检查Twitter更新
• <code>setinterval 秒数</code> - 设置检查间隔

🔧 <b>功能开关:</b>
• <code>toggle verify</code> - 入群验证开关
• <code>toggle ad</code> - 广告检测开关
• <code>toggle reply</code> - 智能回复开关
• <code>toggle twitter</code> - 推文自动转发开关"""

            # 功能状态
            verify_status = "✅" if self.verification_enabled else "❌"
            ad_status = "✅" if self.ad_detection_enabled else "❌"
            reply_status = "✅" if self.auto_reply_enabled else "❌"
            twitter_status = "✅" if self.twitter_auto_forward_enabled else "❌"
            
            help_message += f"""

📝 <b>支持的URL格式:</b>
• https://twitter.com/用户名/status/推文ID
• https://x.com/用户名/status/推文ID

🔧 <b>当前配置:</b>
• 监控用户: @{Config.TWITTER_USERNAME}
• 检查间隔: {self.twitter_check_interval // 3600} 小时
• 入群验证: {verify_status}
• 广告检测: {ad_status}
• 智能回复: {reply_status}
• 推文自动转发: {twitter_status}"""

            await context.bot.send_message(
                chat_id=chat_id,
                text=help_message,
                parse_mode='HTML'
            )
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"发送帮助信息失败: {e}")
            self.stats['errors'] += 1

    async def handle_check_command(self, chat_id, context):
        """立即检查Twitter更新"""
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔍 正在检查 @{Config.TWITTER_USERNAME} 的新推文...",
                parse_mode='HTML'
            )
            
            # 重置上次检查时间以强制检查
            self.last_twitter_check_time = None
            prev_auto_forward = self.twitter_auto_forward_enabled
            try:
                self.twitter_auto_forward_enabled = True
                await self.check_twitter_updates()
            finally:
                self.twitter_auto_forward_enabled = prev_auto_forward
            
            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ 检查完成",
                parse_mode='HTML'
            )
            self.stats['commands_processed'] += 1
            self._log_activity('manual_check', f"由管理员触发")
            
        except Exception as e:
            logger.error(f"手动检查失败: {e}")
            self.stats['errors'] += 1

    async def handle_setinterval_command(self, chat_id, context, interval_str):
        """设置Twitter检查间隔"""
        try:
            interval = int(interval_str)
            if interval < 60:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ 检查间隔不能小于60秒",
                    parse_mode='HTML'
                )
                return
            
            if interval > 86400:  # 24小时
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ 检查间隔不能大于86400秒(24小时)",
                    parse_mode='HTML'
                )
                return
            
            old_interval = self.twitter_check_interval
            self.twitter_check_interval = interval
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ 检查间隔已更新\n\n• 旧间隔: {old_interval} 秒\n• 新间隔: {interval} 秒",
                parse_mode='HTML'
            )
            self.stats['commands_processed'] += 1
            self._log_activity('interval_changed', f"{old_interval}s -> {interval}s")
            
        except ValueError:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ 请输入有效的数字，例如: setinterval 300",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"设置间隔失败: {e}")
            self.stats['errors'] += 1

    async def check_business_intro_schedule(self):
        """检查是否需要发送定时业务介绍"""
        try:
            now = datetime.now()

            # 检查是否到了整点时间（每3小时：0, 3, 6, 9, 12, 15, 18, 21点）
            if now.hour % 3 == 0 and now.minute == 0:
                # 避免重复发送（在同一分钟内）
                if (self.last_business_intro_time and
                    (now - self.last_business_intro_time).total_seconds() < 60):
                    return

                business_intro_message = """🌟 <b>露老师门槛群介绍</b> 🌟

小助理下单机器人： 👉https://t.me/Lulaoshi_bot

※平台是自助入群，机器人下单即可。

如果不太会使用平台，或者遇到任何问题，可以私信露老师：@mteacherlu （不接受闲聊，请理解）

除门槛相关露老师个人电报私信不接受闲聊，禁砍价，不强迫入门，也请保持基本礼貌，感谢理解。

<b>注意事项：</b>
1.露老师不做线下服务，如果有线下相关问题，请私信询问。
2.因个人原因退群后不再重新拉群，还请注意一下。
3.支付过程中如有任何问题，也欢迎私信我，我会尽力帮助。

感谢大家的配合和支持！✨

---------------------------------------------------

<b>相关群组与定制介绍：</b>

<b>日常群：</b>稳定更新，露老师个人原创作品，会更新长视频以及多量照片，都是推特所看不到的内容。

<b>女女群：</b>稳定更新，除露老师外还可以看到另外几位女主，露老师与其他女主合作视频等。

<b>第三视角群：</b>不定期更新，每次活动拍摄由男友视角随心拍摄（还没入日常群和女女群的不推荐首次就购买第三视角群）。

<b>定制视频：</b>根据需求定制露老师视频，可SOLO、FM、FF、FFM、FMM，可按要求使用各种玩具和剧情设计。

小助理下单机器人： 👉https://t.me/Lulaoshi_bot

※希望得到更详细介绍询问请私信"""

                # 删除上一次的业务介绍消息
                if self.last_business_intro_message_id:
                    try:
                        await self.application.bot.delete_message(
                            chat_id=self.chat_id,
                            message_id=self.last_business_intro_message_id
                        )
                        logger.info(f"🗑️ 已删除上一次的业务介绍消息 (消息ID: {self.last_business_intro_message_id})")
                    except Exception as e:
                        logger.warning(f"删除上一次业务介绍消息失败: {e}")

                # 发送新的业务介绍消息
                sent_message = await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=business_intro_message,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )

                # 保存新消息的ID
                if sent_message:
                    self.last_business_intro_message_id = sent_message.message_id
                    logger.info(f"💾 已保存新业务介绍消息ID: {sent_message.message_id}")

                self.last_business_intro_time = now
                logger.info(f"📢 定时发送业务介绍 (时间: {now.strftime('%H:%M')})")

        except Exception as e:
            logger.error(f"定时业务介绍发送失败: {e}")

    async def start_bot(self):
        """启动机器人"""
        try:
            logger.info("🚀 启动TeleLuX机器人...")
            logger.info(f"📱 群组ID: {self.chat_id}")
            
            # 创建应用
            self.application = Application.builder().token(self.bot_token).build()
            
            # 添加消息处理器 - 处理所有文本消息
            message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            self.application.add_handler(message_handler)

            # 添加群组成员变化处理器
            chat_member_handler = ChatMemberHandler(self.handle_chat_member, ChatMemberHandler.CHAT_MEMBER)
            self.application.add_handler(chat_member_handler)
            
            # 启动机器人
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            logger.info("✅ 机器人已启动")
            
        except Exception as e:
            logger.error(f"启动失败: {e}")
            raise
    
    async def stop_bot(self):
        """停止机器人"""
        try:
            if self.application:
                logger.info("停止机器人...")
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("机器人已停止")
        except Exception as e:
            logger.error(f"停止失败: {e}")

async def main():
    """主函数"""
    try:
        logger.info("🚀 TeleLuX完整版启动")
        
        # 验证配置
        Config.validate()
        logger.info("✅ 配置验证通过")
        
        # 创建机器人
        bot = TeleLuXBot()
        
        # 初始化数据库
        bot.database = Database()
        logger.info("✅ 数据库初始化完成")
        
        # 初始化Twitter监控
        bot.twitter_monitor = TwitterMonitor()
        logger.info("✅ Twitter监控初始化完成")
        
        # 启动机器人
        await bot.start_bot()
        
        # 发送启动通知
        startup_message = None
        
        logger.info(f"🐦 Twitter监控已启动: @{Config.TWITTER_USERNAME}, 间隔: {bot.twitter_check_interval}秒")
        logger.info("💡 私聊机器人发送 'help' 查看所有命令")
        
        # 保持运行并定期检查
        try:
            while True:
                # 检查Twitter更新
                await bot.check_twitter_updates()
                
                # 检查定时业务介绍
                await bot.check_business_intro_schedule()

                await asyncio.sleep(30)  # 每30秒检查一次
        except KeyboardInterrupt:
            logger.info("\n⏹️  收到停止信号")
        finally:
            # 发送停止通知
            try:
                await bot.application.bot.send_message(
                    chat_id=bot.chat_id,
                    text="🛑 TeleLuX完整版系统已停止",
                    parse_mode='HTML'
                )
            except:
                pass
            
            await bot.stop_bot()
            logger.info("✅ 系统已停止")
        
    except Exception as e:
        logger.error(f"❌ 系统运行失败: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 系统已停止")
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
