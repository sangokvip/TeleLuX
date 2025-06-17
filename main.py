#!/usr/bin/env python3
"""
TeleLuX - Twitter监控和Telegram通知系统
完整版系统，包含所有功能
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
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
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理收到的消息"""
        try:
            message_text = update.message.text.strip() if update.message.text else ""
            chat_type = update.effective_chat.type
            chat_id = update.effective_chat.id
            user_name = update.effective_user.username or update.effective_user.first_name
            
            logger.info(f"收到消息: '{message_text}' 来自: {user_name} (Chat ID: {chat_id}, 类型: {chat_type})")
            
            # 处理私聊消息
            if chat_type == 'private':
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
                    
                    logger.info(f"🎉 收到私聊触发词'27'，已向群组发送业务介绍消息 (来自用户: {user_name})")
                else:
                    # 对其他私聊消息给予提示
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="👋 你好！如需发送业务介绍到群组，请发送 '27'",
                        parse_mode='HTML'
                    )
                    logger.info(f"收到私聊消息'{message_text}'，已回复提示信息 (来自用户: {user_name})")
            # 处理群组消息（获取最新推文）
            elif str(chat_id) == str(self.chat_id):
                if self.twitter_monitor:
                    username = Config.TWITTER_USERNAME
                    logger.info(f"群组消息触发，获取 @{username} 的最新推文...")
                    
                    try:
                        latest_tweets = self.twitter_monitor.get_latest_tweets(username, count=1)
                        
                        if latest_tweets:
                            tweet = latest_tweets[0]
                            
                            # 发送最新推文
                            message = f"""
🐦 <b>@{username} 的最新推文</b>

📝 <b>内容:</b> {self._escape_html(tweet['text'])}
🕒 <b>时间:</b> {tweet['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}

🔗 <a href="{tweet['url']}">查看原推文</a>
                            """.strip()
                            
                            await context.bot.send_message(
                                chat_id=self.chat_id,
                                text=message,
                                parse_mode='HTML',
                                disable_web_page_preview=False
                            )
                            
                            logger.info("成功发送最新推文")
                        else:
                            await context.bot.send_message(
                                chat_id=self.chat_id,
                                text=f"⚠️ 暂时无法获取 @{username} 的推文",
                                parse_mode='HTML'
                            )
                    except Exception as e:
                        logger.error(f"获取推文失败: {e}")
                        await context.bot.send_message(
                            chat_id=self.chat_id,
                            text="⚠️ 获取推文时发生错误",
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

            # 检查是否有新用户加入
            if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator', 'creator']:
                user_name = user.first_name or user.username or "新朋友"

                welcome_message = f"欢迎 <b>{self._escape_html(user_name)}</b> 光临露老师的聊天群 🎉"

                await context.bot.send_message(
                    chat_id=self.chat_id,
                    text=welcome_message,
                    parse_mode='HTML'
                )

                logger.info(f"👋 发送欢迎消息给新用户: {user_name} (ID: {user.id})")

        except Exception as e:
            logger.error(f"处理群组成员变化时发生错误: {e}")

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
    
    async def check_tweets_periodically(self):
        """定期检查推文"""
        try:
            if not self.last_check_time:
                self.last_check_time = datetime.now()
                return
            
            # 检查是否到了检查时间（每50分钟检查一次）
            time_diff = (datetime.now() - self.last_check_time).total_seconds()
            if time_diff < Config.CHECK_INTERVAL:
                return
            
            logger.info("执行定时推文检查...")
            self.last_check_time = datetime.now()
            
            # 检查新推文
            new_tweets = self.twitter_monitor.check_new_tweets(Config.TWITTER_USERNAME)
            
            # 发送通知
            for tweet in new_tweets:
                message = f"""
🐦 <b>新推文通知</b>

👤 <b>用户:</b> @{tweet['username']}
📝 <b>内容:</b> {self._escape_html(tweet['text'])}
🕒 <b>时间:</b> {tweet['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}

🔗 <a href="{tweet['url']}">查看原推文</a>
                """.strip()
                
                await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                )
                
                logger.info(f"✅ 推文通知发送成功: {tweet['url']}")
            
            # 记录检查结果
            if new_tweets:
                logger.info(f"🎉 本次检查发现并处理了 {len(new_tweets)} 条新推文")
            else:
                logger.info("📊 本次检查未发现新推文")
                
        except Exception as e:
            logger.error(f"定期检查推文失败: {e}")

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

                await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=business_intro_message,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )

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
        startup_message = f"""🚀 TeleLuX完整版已启动！

📊 <b>配置信息:</b>
• 监控账号: @{Config.TWITTER_USERNAME}
• 检查间隔: {Config.CHECK_INTERVAL}秒
• 自动欢迎: 已启用
• 定时业务介绍: 每3小时整点

💡 <b>功能说明:</b>
1. 自动监控推文并发送通知
2. 在群组中发送任意消息，机器人会自动回复最新推文
3. 私聊机器人发送'27'，会向群组发送业务介绍
4. 新用户加入时自动发送欢迎消息
5. 每3小时整点自动发送业务介绍

🎉 <b>系统状态:</b> 运行中"""
        
        await bot.application.bot.send_message(
            chat_id=bot.chat_id,
            text=startup_message,
            parse_mode='HTML'
        )
        
        logger.info("💡 现在可以私聊机器人发送'27'或在群组发送消息测试功能！")
        
        # 保持运行并定期检查推文
        try:
            while True:
                # 定期检查推文
                await bot.check_tweets_periodically()

                # 检查定时业务介绍
                await bot.check_business_intro_schedule()

                await asyncio.sleep(1)
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
