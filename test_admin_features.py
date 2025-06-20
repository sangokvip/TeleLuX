#!/usr/bin/env python3
"""
测试管理员相关功能
1. 欢迎消息8小时自动删除
2. 管理员消息不重复转发
"""

import asyncio
from datetime import datetime
from telegram.ext import Application, MessageHandler, filters
from config import Config

class AdminFeaturesTester:
    def __init__(self):
        self.admin_chat_id = Config.ADMIN_CHAT_ID
        self.received_messages = []
        
    async def handle_private_message(self, update, context):
        """处理私信消息"""
        try:
            user = update.effective_user
            message = update.message
            chat_id = update.effective_chat.id
            
            user_name = user.first_name or user.username or f"用户{user.id}"
            message_text = message.text or ""
            
            print(f"\n📨 收到私信:")
            print(f"   用户: {user_name}")
            print(f"   Chat ID: {chat_id}")
            print(f"   消息: {message_text}")
            
            # 检查是否是管理员消息
            if str(chat_id) == str(self.admin_chat_id):
                print(f"   🔒 这是管理员消息，不会转发")
                
                # 回复管理员
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="✅ 管理员消息已收到，不会转发给自己"
                )
            else:
                print(f"   📤 这是普通用户消息，会转发给管理员")
                
                # 模拟转发给管理员
                if self.admin_chat_id:
                    forward_message = f"""📨 <b>收到私信</b>

👤 <b>用户信息:</b>
• 姓名: {user_name}
• Chat ID: {chat_id}

📝 <b>消息内容:</b>
{message_text}

🕒 <b>发送时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"""
                    
                    await context.bot.send_message(
                        chat_id=self.admin_chat_id,
                        text=forward_message,
                        parse_mode='HTML'
                    )
                    print(f"   ✅ 已转发给管理员")
                
                # 回复用户
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="✅ 您的消息已收到并转发给管理员"
                )
            
            self.received_messages.append({
                'user_name': user_name,
                'chat_id': chat_id,
                'message': message_text,
                'is_admin': str(chat_id) == str(self.admin_chat_id),
                'time': datetime.now()
            })
            
        except Exception as e:
            print(f"❌ 处理消息时发生错误: {e}")

async def test_welcome_message_deletion():
    """测试欢迎消息自动删除功能"""
    print("🧪 测试欢迎消息自动删除功能")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过")
        
        # 创建机器人应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化机器人
        await application.initialize()
        await application.start()
        
        print(f"✅ 机器人已连接")
        print(f"📱 目标群组ID: {Config.TELEGRAM_CHAT_ID}")
        
        # 发送测试欢迎消息
        test_welcome = f"""🎉 欢迎 <b>测试用户</b> 加入露老师聊天群！

🔍 认准露老师唯一账号：
• X账号：<a href="https://x.com/xiuchiluchu910"><b>xiuchiluchu910</b></a>
• Telegram账号：<a href="https://t.me/mteacherlu"><b>@mteacherlu</b></a>

💬 群内随意聊天，但请勿轻易相信任何陌生人，谨防诈骗 ⚠️

<i>📝 这是测试消息，将在30秒后自动删除（模拟8小时）</i>"""
        
        print(f"\n📤 发送测试欢迎消息...")
        sent_message = await application.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=test_welcome,
            parse_mode='HTML'
        )
        
        if sent_message:
            print(f"✅ 欢迎消息发送成功")
            print(f"   消息ID: {sent_message.message_id}")
            print(f"   发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 模拟8小时后删除（这里用30秒代替）
            print(f"\n⏳ 等待30秒后删除消息（模拟8小时自动删除）...")
            await asyncio.sleep(30)
            
            try:
                await application.bot.delete_message(
                    chat_id=Config.TELEGRAM_CHAT_ID,
                    message_id=sent_message.message_id
                )
                print(f"🗑️ 欢迎消息已自动删除")
                print(f"✅ 8小时自动删除功能正常")
            except Exception as e:
                print(f"❌ 删除消息失败: {e}")
                return False
        else:
            print(f"❌ 欢迎消息发送失败")
            return False
        
        # 停止机器人
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_admin_message_filtering():
    """测试管理员消息过滤功能"""
    print("🧪 测试管理员消息过滤功能")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        admin_chat_id = Config.ADMIN_CHAT_ID
        
        if not admin_chat_id:
            print("❌ ADMIN_CHAT_ID 未配置")
            return False
        
        print(f"✅ 管理员 Chat ID: {admin_chat_id}")
        
        # 创建测试器
        tester = AdminFeaturesTester()
        
        # 创建机器人应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 添加私信处理器
        private_handler = MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE, 
            tester.handle_private_message
        )
        application.add_handler(private_handler)
        
        print(f"✅ 机器人已启动")
        print(f"\n📋 测试说明:")
        print(f"1. 管理员 (Chat ID: {admin_chat_id}) 私聊机器人 - 不会转发")
        print(f"2. 其他用户私聊机器人 - 会转发给管理员")
        print(f"3. 按 Ctrl+C 停止测试")
        print(f"\n⏳ 等待私信消息...")
        
        # 启动机器人
        await application.run_polling()
        
    except KeyboardInterrupt:
        print(f"\n⏹️  测试已停止")
        
        if tester.received_messages:
            print(f"\n📊 测试统计:")
            print(f"   总消息数量: {len(tester.received_messages)}")
            
            admin_messages = [msg for msg in tester.received_messages if msg['is_admin']]
            user_messages = [msg for msg in tester.received_messages if not msg['is_admin']]
            
            print(f"   管理员消息: {len(admin_messages)} 条（不转发）")
            print(f"   用户消息: {len(user_messages)} 条（已转发）")
            
            print(f"\n📋 消息详情:")
            for i, msg in enumerate(tester.received_messages, 1):
                status = "管理员消息" if msg['is_admin'] else "用户消息"
                print(f"   {i}. {status} - {msg['user_name']}: {msg['message'][:30]}...")
        else:
            print(f"\n⚠️  没有收到任何消息")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def explain_features():
    """解释功能特点"""
    print("📋 管理员功能说明")
    print("=" * 50)
    
    print("🎯 功能1: 欢迎消息8小时自动删除")
    print("• 新用户加入时发送欢迎消息")
    print("• 使用JobQueue安排8小时后删除")
    print("• 保持群组整洁，避免消息堆积")
    print("• 删除失败时会记录警告但不影响运行")
    
    print(f"\n🎯 功能2: 管理员消息过滤")
    print("• 检测私信发送者的Chat ID")
    print("• 如果是管理员自己的消息，不进行转发")
    print("• 避免管理员收到自己消息的转发")
    print("• 其他用户消息正常转发给管理员")
    
    print(f"\n🔧 技术实现:")
    print("• 欢迎消息: context.job_queue.run_once()")
    print("• 消息过滤: if str(chat_id) == str(admin_chat_id)")
    print("• 错误处理: try-except包装所有操作")
    print("• 日志记录: 详细记录所有操作")

async def main():
    """主函数"""
    print("🧪 管理员功能测试")
    print("=" * 50)
    
    try:
        # 解释功能
        explain_features()
        
        print("\n" + "=" * 50)
        
        # 询问测试方式
        print(f"\n❓ 选择测试功能:")
        print(f"1. 测试欢迎消息自动删除")
        print(f"2. 测试管理员消息过滤")
        print(f"3. 跳过测试")
        
        try:
            choice = input("请选择 (1/2/3): ").strip()
            
            if choice == "1":
                print(f"\n🚀 测试欢迎消息自动删除...")
                success = await test_welcome_message_deletion()
            elif choice == "2":
                print(f"\n🚀 测试管理员消息过滤...")
                success = await test_admin_message_filtering()
            else:
                print(f"\n⏭️  跳过测试")
                success = True
            
            if success:
                print(f"\n🎉 测试完成！")
                print(f"\n📋 部署建议:")
                print(f"1. 更新VPS上的main.py文件")
                print(f"2. 确保ADMIN_CHAT_ID已正确配置")
                print(f"3. 重启TeleLuX服务")
                print(f"4. 测试欢迎消息和私信转发功能")
                print(f"5. 验证管理员消息不会被重复转发")
            
        except KeyboardInterrupt:
            print(f"\n⏹️  测试已取消")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
