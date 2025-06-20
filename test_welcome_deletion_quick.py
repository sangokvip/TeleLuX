#!/usr/bin/env python3
"""
快速测试欢迎消息删除功能（2分钟删除）
"""

import asyncio
from datetime import datetime
from telegram.ext import Application, ChatMemberHandler, MessageHandler, filters
from config import Config

class QuickWelcomeTester:
    def __init__(self):
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.application = None
        
    async def _delete_welcome_message(self, context):
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
            
            print(f"🗑️ 已删除用户 {user_name} 的欢迎消息 (消息ID: {message_id})")
            
        except Exception as e:
            print(f"❌ 删除欢迎消息失败: {e}")
    
    async def handle_message(self, update, context):
        """处理消息，模拟新用户加入"""
        try:
            message = update.message
            user = update.effective_user
            chat = update.effective_chat
            
            # 只处理群组消息
            if chat.type not in ['group', 'supergroup']:
                return
            
            # 只处理目标群组
            if str(chat.id) != str(self.chat_id):
                return
            
            # 检查是否是测试命令
            if message.text and message.text.strip().lower() == '/test_welcome':
                user_name = user.first_name or user.username or "测试用户"
                
                # 发送测试欢迎消息
                welcome_message = f"""🎉 欢迎 <b>{user_name}</b> 加入露老师聊天群！

🔍 认准露老师唯一账号：
• X账号：<a href="https://x.com/xiuchiluchu910"><b>xiuchiluchu910</b></a>
• Telegram账号：<a href="https://t.me/mteacherlu"><b>@mteacherlu</b></a>

💬 群内随意聊天，但请勿轻易相信任何陌生人，谨防诈骗 ⚠️

<i>📝 这是测试消息，将在2分钟后自动删除</i>"""
                
                sent_message = await context.bot.send_message(
                    chat_id=self.chat_id,
                    text=welcome_message,
                    parse_mode='HTML'
                )
                
                print(f"✅ 发送测试欢迎消息: {user_name} (消息ID: {sent_message.message_id})")
                
                # 安排2分钟后删除消息
                if sent_message and context.job_queue:
                    try:
                        context.job_queue.run_once(
                            self._delete_welcome_message,
                            when=120,  # 2分钟 = 120秒
                            data={
                                'chat_id': self.chat_id,
                                'message_id': sent_message.message_id,
                                'user_name': user_name
                            }
                        )
                        print(f"⏰ 已安排2分钟后删除欢迎消息 (消息ID: {sent_message.message_id})")
                        
                        # 发送确认消息
                        await context.bot.send_message(
                            chat_id=self.chat_id,
                            text=f"⏰ 测试开始！欢迎消息将在2分钟后自动删除\n消息ID: {sent_message.message_id}",
                            reply_to_message_id=sent_message.message_id
                        )
                        
                    except Exception as e:
                        print(f"❌ 安排删除失败: {e}")
                        await context.bot.send_message(
                            chat_id=self.chat_id,
                            text=f"❌ 安排自动删除失败: {e}"
                        )
                else:
                    print("❌ JobQueue不可用或消息发送失败")
                    
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")

async def test_quick_welcome_deletion():
    """快速测试欢迎消息删除功能"""
    print("🧪 快速测试欢迎消息删除功能")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过")
        print(f"📱 群组ID: {Config.TELEGRAM_CHAT_ID}")
        
        # 创建测试器
        tester = QuickWelcomeTester()
        
        # 创建应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        tester.application = application
        
        # 添加消息处理器
        message_handler = MessageHandler(filters.TEXT, tester.handle_message)
        application.add_handler(message_handler)
        
        print("✅ 机器人已启动")
        print("\n📋 测试说明:")
        print("1. 在群组中发送 /test_welcome 触发测试")
        print("2. 机器人会发送欢迎消息")
        print("3. 2分钟后自动删除欢迎消息")
        print("4. 按 Ctrl+C 停止测试")
        print("\n⏳ 等待测试命令...")
        
        # 启动机器人
        await application.run_polling()
        
    except KeyboardInterrupt:
        print(f"\n⏹️  测试已停止")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_direct_deletion():
    """直接测试删除功能"""
    print("🗑️ 直接测试删除功能")
    print("=" * 50)
    
    try:
        # 创建应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化
        await application.initialize()
        await application.start()
        
        print("✅ 应用已启动")
        
        # 发送测试消息
        test_message = "🧪 直接删除测试消息 - 将在30秒后删除"
        
        sent_message = await application.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=test_message
        )
        
        if sent_message:
            print(f"✅ 测试消息发送成功 (ID: {sent_message.message_id})")
            
            # 使用JobQueue安排删除
            async def delete_job(context):
                try:
                    await context.bot.delete_message(
                        chat_id=Config.TELEGRAM_CHAT_ID,
                        message_id=sent_message.message_id
                    )
                    print("✅ 消息删除成功")
                except Exception as e:
                    print(f"❌ 消息删除失败: {e}")
            
            # 安排30秒后删除
            application.job_queue.run_once(delete_job, when=30)
            print("⏰ 已安排30秒后删除消息...")
            
            # 等待删除
            await asyncio.sleep(35)
            
        # 停止应用
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("🧪 欢迎消息删除功能快速测试")
    print("=" * 50)
    
    try:
        print("❓ 选择测试方式:")
        print("1. 交互式测试 - 在群组中发送 /test_welcome")
        print("2. 直接测试 - 发送消息并自动删除")
        print("3. 跳过测试")
        
        choice = input("请选择 (1/2/3): ").strip()
        
        if choice == "1":
            print("\n🚀 启动交互式测试...")
            success = await test_quick_welcome_deletion()
        elif choice == "2":
            print("\n🚀 启动直接测试...")
            success = await test_direct_deletion()
        else:
            print("\n⏭️  跳过测试")
            success = True
        
        if success:
            print(f"\n🎉 测试完成！")
            print(f"\n📋 如果测试成功，说明欢迎消息自动删除功能正常")
            print(f"\n💡 可能的问题:")
            print(f"1. 8小时太长，难以观察到效果")
            print(f"2. 系统重启会清除JobQueue任务")
            print(f"3. 机器人权限不足")
            print(f"\n🔧 建议:")
            print(f"1. 检查机器人是否有管理员权限")
            print(f"2. 观察系统日志中的删除记录")
            print(f"3. 如需快速验证，可临时修改删除时间")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
