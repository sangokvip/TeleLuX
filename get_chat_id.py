#!/usr/bin/env python3
"""
获取用户的 chat_id
"""

import asyncio
from telegram.ext import Application, MessageHandler, filters
from config import Config

class ChatIdCollector:
    def __init__(self):
        self.chat_ids = {}
        
    async def handle_message(self, update, context):
        """处理收到的消息，记录用户的chat_id"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            if chat.type == 'private':  # 只处理私聊消息
                user_info = {
                    'chat_id': chat.id,
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
                
                print(f"\n📨 收到私聊消息:")
                print(f"   Chat ID: {chat.id}")
                print(f"   User ID: {user.id}")
                print(f"   用户名: @{user.username}")
                print(f"   姓名: {user.first_name} {user.last_name or ''}")
                print(f"   消息: {update.message.text}")
                
                # 如果是 bryansuperb，特别标记
                if user.username and user.username.lower() == 'bryansuperb':
                    print(f"🎯 找到 bryansuperb 的 Chat ID: {chat.id}")
                    
                    # 发送确认消息
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=f"✅ 已记录您的 Chat ID: {chat.id}\n\n这个ID将用于接收用户活动监控通知。"
                    )
                
                self.chat_ids[user.username or f"user_{user.id}"] = user_info
                
        except Exception as e:
            print(f"❌ 处理消息时发生错误: {e}")

async def main():
    """主函数"""
    print("🔍 Chat ID 收集工具")
    print("=" * 50)
    print("请让 bryansuperb 私聊机器人发送任意消息...")
    print("程序将显示他的 Chat ID")
    print("按 Ctrl+C 停止程序")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过")
        
        # 创建收集器
        collector = ChatIdCollector()
        
        # 创建机器人应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 添加消息处理器
        message_handler = MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, collector.handle_message)
        application.add_handler(message_handler)
        
        # 启动机器人
        print("🤖 机器人已启动，等待消息...")
        await application.run_polling()
        
    except KeyboardInterrupt:
        print(f"\n⏹️  程序已停止")
        
        if collector.chat_ids:
            print(f"\n📋 收集到的 Chat ID:")
            for username, info in collector.chat_ids.items():
                print(f"   @{username}: {info['chat_id']}")
        else:
            print(f"\n⚠️  没有收集到任何 Chat ID")
            
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
