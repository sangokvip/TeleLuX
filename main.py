#!/usr/bin/env python3
"""
TeleLuX - Twitter监控和Telegram通知系统
完整版系统，包含所有功能
"""

import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, ChatMemberHandler, filters, ContextTypes
from config import Config
from twitter_monitor import TwitterMonitor
from database import Database

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
        self.user_activity_log = {}  # 记录用户进群退群活动
        self.welcome_messages = []  # 记录所有欢迎消息ID
        
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
                            tweet_info = self.twitter_monitor.get_tweet_by_id(tweet_id)

                            if tweet_info:
                                # 发送到群组
                                tweet_message = f"""
🐦 <b>推文分享</b>

👤 <b>用户:</b> @{tweet_info['username']}
📝 <b>内容:</b> {self._escape_html(tweet_info['text'])}
🕒 <b>时间:</b> {tweet_info['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}

🔗 <a href=\"{tweet_info['url']}\">查看原推文</a>
                                """.strip()

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
                # 群组消息不再触发推文获取，只记录日志
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
                # 获取用户信息（如果在活动日志中）
                user_info = ""
                if user_id in self.user_activity_log:
                    user_data = self.user_activity_log[user_id]
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

            # 记录用户活动
            if user_id not in self.user_activity_log:
                self.user_activity_log[user_id] = {
                    'user_name': user_name,
                    'username': username,
                    'join_times': [],
                    'leave_times': [],
                    'total_joins': 0,
                    'total_leaves': 0
                }

            # 更新用户信息（可能会变化）
            self.user_activity_log[user_id]['user_name'] = user_name
            self.user_activity_log[user_id]['username'] = username

            # 检查用户加入
            if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator', 'creator']:
                # 记录加入时间
                self.user_activity_log[user_id]['join_times'].append(current_time)
                self.user_activity_log[user_id]['total_joins'] += 1

                logger.info(f"👋 用户加入: {user_name} (ID: {user_id}, 用户名: @{username})")

                # 检查是否是重复进群用户（超过1次才通知）
                if self.user_activity_log[user_id]['total_joins'] > 1:
                    await self._notify_repeat_user(user_id, 'join', context)

                # 发送欢迎消息
                welcome_message = f"""🎉 欢迎 <b>{self._escape_html(user_name)}</b> 加入露老师聊天群！

🔍 认准露老师唯一账号：
• X账号：<a href="https://x.com/xiuchiluchu910"><b>xiuchiluchu910</b></a>
• Telegram账号：<a href="https://t.me/mteacherlu"><b>@mteacherlu</b></a>

💬 群内随意聊天，但请勿轻易相信任何陌生人，谨防诈骗 ⚠️"""

                sent_message = await context.bot.send_message(
                    chat_id=self.chat_id,
                    text=welcome_message,
                    parse_mode='HTML'
                )

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

                # 安排1分钟后删除消息
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
                self.user_activity_log[user_id]['leave_times'].append(current_time)
                self.user_activity_log[user_id]['total_leaves'] += 1

                logger.info(f"👋 用户离开: {user_name} (ID: {user_id}, 用户名: @{username})")

                # 检查是否是第二次离开，如果是则加入黑名单
                if self.user_activity_log[user_id]['total_leaves'] >= 2:
                    # 添加到黑名单（移除黑名单检查，确保每次第二次离开都加入）
                    success = self.database.add_to_blacklist(
                        user_id=user_id,
                        user_name=user_name,
                        username=username,
                        leave_count=self.user_activity_log[user_id]['total_leaves'],
                        reason=f"多次离群 ({self.user_activity_log[user_id]['total_leaves']}次)"
                    )
                    
                    if success:
                        # 通知管理员用户已被加入黑名单
                        await self._notify_user_blacklisted(user_id, context)
                        logger.info(f"🚫 用户 {user_name} (ID: {user_id}) 因多次离群已自动加入黑名单")

                # 如果用户离开超过1次，通知管理员
                if self.user_activity_log[user_id]['total_leaves'] > 1:
                    await self._notify_repeat_user(user_id, 'leave', context)

        except Exception as e:
            logger.error(f"处理群组成员变化时发生错误: {e}")

    async def _notify_repeat_user(self, user_id, action, context):
        """通知管理员用户的重复进群/退群行为"""
        try:
            user_data = self.user_activity_log[user_id]
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
            user_data = self.user_activity_log[user_id]
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

    def _is_twitter_url(self, text):
        """检查文本是否包含Twitter URL"""
        import re

        # Twitter URL模式
        twitter_patterns = [
            r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
            r'https?://(?:www\.)?x\.com/\w+/status/\d+',
            r'twitter\.com/\w+/status/\d+',
            r'x\.com/\w+/status/\d+'
        ]

        for pattern in twitter_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_tweet_id(self, url):
        """从Twitter URL中提取推文ID"""
        import re

        # 提取推文ID的模式
        patterns = [
            r'(?:twitter|x)\.com/\w+/status/(\d+)',
            r'/status/(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    


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

                business_intro_message = """🌟 <b>露老师业务介绍</b> 🌟

小助理下单机器人： 👉https://t.me/Lulaoshi_bot

※平台是自助入群，机器人下单即可。

如果不太会使用平台，或者遇到任何问题，可以私信我，或者私信露老师截图扫码支付：@mteacherlu。

除门槛相关露老师个人电报私信不接受闲聊，禁砍价，不强迫入门，也请保持基本礼貌，感谢理解。

<b>注意事项：</b>
1.露老师不做线下服务，如果有线下相关问题，请私信我询问。
2.因个人原因退群后不再重新拉群，还请注意一下。
3.支付过程中如有任何问题，也欢迎私信我，我会尽力帮助。

感谢大家的配合和支持！✨

---------------------------------------------------

<b>相关群组与定制介绍：</b>

<b>日常群：</b>稳定更新，露老师个人原创作品，会更新长视频以及多量照片，都是推特所看不到的内容。

<b>女女群：</b>稳定更新，除露老师外还可以看到另外几位女主，露老师与其他女主合作视频等。

<b>三视角群：</b>不定期更新，每次活动拍摄由男友视角随心拍摄。

<b>定制视频：</b>根据需求定制露老师视频，可SOLO、FM、FF、FFM、FMM，可按要求使用各种玩具和剧情设计。

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
        startup_message = f"""🚀 TeleLuX推文分享版已启动！

📊 <b>功能说明:</b>
• 自动欢迎新用户 (1分钟后自动删除)
• 定时业务介绍: 每3小时整点 (自动删除上一条)
• Twitter推文分享功能
• 用户进群退群行为监控
• 私信消息转发给管理员

💡 <b>私聊功能:</b>
• 发送 '27' - 向群组发送业务介绍
• 发送 'clear' - 清除群内所有欢迎消息
• 发送 Twitter URL - 分享推文到群组

📝 <b>支持的URL格式:</b>
• https://twitter.com/用户名/status/推文ID
• https://x.com/用户名/status/推文ID

🎉 <b>系统状态:</b> 运行中"""
        
        await bot.application.bot.send_message(
            chat_id=bot.chat_id,
            text=startup_message,
            parse_mode='HTML'
        )
        
        logger.info("💡 现在可以私聊机器人发送'27'(业务介绍)或Twitter URL(分享推文)！")
        
        # 保持运行并定期检查定时业务介绍
        try:
            while True:
                # 检查定时业务介绍
                await bot.check_business_intro_schedule()

                await asyncio.sleep(60)  # 每分钟检查一次定时任务
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
