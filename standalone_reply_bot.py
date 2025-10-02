#!/usr/bin/env python3
"""
独立的回复机器人 - 专门处理回复功能
"""

import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StandaloneReplyBot:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.admin_chat_id = Config.ADMIN_CHAT_ID
        self.application = None
        
    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理私信并转发给管理员"""
        try:
            chat_type = update.effective_chat.type
            
            # 只处理私聊消息
            if chat_type != 'private':
                return
            
            user = update.effective_user
            message = update.message
            chat_id = update.effective_chat.id
            
            # 检查是否是管理员自己发送的消息
            if str(chat_id) == str(self.admin_chat_id):
                logger.info(f"收到管理员消息，不进行转发")
                return
            
            # 获取用户信息
            user_name = user.first_name or user.username or f"用户{user.id}"
            username = user.username or "无用户名"
            user_id = user.id
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

🕒 <b>发送时间:</b> {message_time}"""

            # 创建回复按钮
            keyboard = [
                [
                    InlineKeyboardButton("💬 快速回复", callback_data=f"reply_{chat_id}"),
                    InlineKeyboardButton("📋 复制Chat ID", callback_data=f"copy_{chat_id}")
                ],
                [
                    InlineKeyboardButton("🚫 忽略", callback_data=f"ignore_{chat_id}"),
                    InlineKeyboardButton("⚠️ 标记可疑", callback_data=f"suspicious_{chat_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # 发送转发消息给管理员
            await context.bot.send_message(
                chat_id=self.admin_chat_id,
                text=forward_message,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            logger.info(f"📨 已转发私信给管理员: {user_name} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"转发私信失败: {e}")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理内联键盘回调"""
        try:
            query = update.callback_query
            await query.answer("✅ 按钮点击已收到")
            
            callback_data = query.data
            
            # 检查是否是管理员操作
            if str(query.from_user.id) != str(self.admin_chat_id):
                await query.edit_message_text("❌ 只有管理员可以使用此功能")
                return
            
            # 解析回调数据
            if '_' in callback_data:
                action, target_chat_id = callback_data.split('_', 1)
                
                if action == "reply":
                    reply_message = f"""💬 <b>回复用户消息</b>

🎯 <b>目标用户 Chat ID:</b> {target_chat_id}

📝 <b>请发送您要回复的消息内容</b>
格式：/reply {target_chat_id} 您的回复内容

💡 <b>示例:</b>
/reply {target_chat_id} 您好，感谢您的咨询！

⚠️ <b>注意:</b> 请确保消息内容准确，发送后无法撤回"""
                    
                    await query.edit_message_text(
                        text=reply_message,
                        parse_mode='HTML'
                    )
                    logger.info(f"处理快速回复按钮: {target_chat_id}")
                    
                elif action == "copy":
                    copy_message = f"""📋 <b>Chat ID 已准备复制</b>

🎯 <b>用户 Chat ID:</b> <code>{target_chat_id}</code>

💡 <b>使用方法:</b>
1. 点击上方的Chat ID进行复制
2. 在任意聊天界面输入复制的ID
3. 发送消息给该用户

📱 <b>或者使用命令:</b>
/reply {target_chat_id} 您的消息内容"""
                    
                    await query.edit_message_text(
                        text=copy_message,
                        parse_mode='HTML'
                    )
                    logger.info(f"处理复制Chat ID按钮: {target_chat_id}")
                    
                elif action == "ignore":
                    ignore_message = f"""🚫 <b>消息已标记为忽略</b>

👤 <b>用户 Chat ID:</b> {target_chat_id}
⏰ <b>操作时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 此消息已被标记为已处理"""
                    
                    await query.edit_message_text(
                        text=ignore_message,
                        parse_mode='HTML'
                    )
                    logger.info(f"标记消息为忽略: {target_chat_id}")
                    
                elif action == "suspicious":
                    suspicious_message = f"""⚠️ <b>用户已标记为可疑</b>

👤 <b>用户 Chat ID:</b> {target_chat_id}
🚨 <b>标记时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👮 <b>操作管理员:</b> {query.from_user.first_name or query.from_user.username}

📝 <b>建议操作:</b>
• 密切关注该用户后续行为
• 必要时可考虑限制或移除
• 记录相关证据以备查证

⚠️ 此用户已被加入监控列表"""
                    
                    await query.edit_message_text(
                        text=suspicious_message,
                        parse_mode='HTML'
                    )
                    logger.warning(f"标记可疑用户: {target_chat_id}")
                    
        except Exception as e:
            logger.error(f"处理回调查询失败: {e}")
            try:
                await query.edit_message_text(f"❌ 处理失败: {str(e)[:100]}")
            except:
                pass

    async def handle_reply_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理回复命令"""
        try:
            # 检查是否是管理员
            if str(update.effective_user.id) != str(self.admin_chat_id):
                await update.message.reply_text("❌ 只有管理员可以使用此命令")
                return
            
            # 解析命令参数
            command_text = update.message.text
            parts = command_text.split(' ', 2)
            
            if len(parts) < 3:
                await update.message.reply_text(
                    "❌ 命令格式错误\n\n💡 正确格式：\n/reply [Chat_ID] [消息内容]\n\n📝 示例：\n/reply 123456789 您好，感谢您的咨询！"
                )
                return
            
            target_chat_id = parts[1]
            reply_content = parts[2]
            
            # 发送回复消息
            await context.bot.send_message(
                chat_id=target_chat_id,
                text=reply_content
            )
            
            # 确认消息
            safe_reply_content = self._escape_html(reply_content)
            confirm_message = f"""✅ <b>回复已发送</b>

🎯 <b>目标用户:</b> {target_chat_id}
📝 <b>回复内容:</b> {safe_reply_content}
⏰ <b>发送时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 消息已成功发送给用户"""
            
            await update.message.reply_text(
                text=confirm_message,
                parse_mode='HTML'
            )
            
            logger.info(f"📨 管理员回复用户: {target_chat_id} - {reply_content[:50]}...")
            
        except Exception as e:
            logger.error(f"处理回复命令失败: {e}")
            await update.message.reply_text(f"❌ 发送回复失败: {str(e)[:100]}")

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

    async def start_bot(self):
        """启动机器人"""
        try:
            logger.info("🚀 启动独立回复机器人...")
            logger.info(f"📱 管理员ID: {self.admin_chat_id}")
            
            # 创建应用
            self.application = Application.builder().token(self.bot_token).build()
            
            # 添加私信处理器
            private_handler = MessageHandler(
                filters.TEXT & filters.ChatType.PRIVATE, 
                self.handle_private_message
            )
            self.application.add_handler(private_handler)
            
            # 添加回复命令处理器
            reply_handler = MessageHandler(filters.Regex(r'^/reply\s+'), self.handle_reply_command)
            self.application.add_handler(reply_handler)
            
            # 添加回调查询处理器
            callback_handler = CallbackQueryHandler(self.handle_callback_query)
            self.application.add_handler(callback_handler)
            
            logger.info("✅ 所有处理器已添加")
            
            # 发送启动通知
            startup_message = f"""🚀 <b>独立回复机器人已启动</b>

📊 <b>功能说明:</b>
• 私信转发给管理员（带回复按钮）
• 一键回复功能
• 消息管理（忽略、标记可疑）

💡 <b>使用方法:</b>
• 点击按钮获取回复指令
• 使用 /reply [Chat_ID] [消息] 回复用户

✅ <b>系统状态:</b> 运行中"""
            
            await self.application.bot.send_message(
                chat_id=self.admin_chat_id,
                text=startup_message,
                parse_mode='HTML'
            )
            
            # 启动机器人
            await self.application.run_polling()
            
        except Exception as e:
            logger.error(f"启动失败: {e}")
            raise

async def main():
    """主函数"""
    try:
        logger.info("🚀 独立回复机器人启动")
        
        # 验证必要的Telegram配置
        Config.require_telegram(require_chat_id=False, require_admin=True)
        logger.info("✅ 配置验证通过")
        
        # 创建机器人
        bot = StandaloneReplyBot()
        
        # 启动机器人
        await bot.start_bot()
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  收到停止信号")
    except Exception as e:
        logger.error(f"❌ 系统运行失败: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 系统已停止")
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
