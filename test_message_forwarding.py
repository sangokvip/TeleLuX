#!/usr/bin/env python3
"""
测试私信转发功能
"""

import asyncio
from datetime import datetime
from telegram.ext import Application, MessageHandler, filters
from config import Config

def _escape_html(text):
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

class MessageForwardingTester:
    def __init__(self):
        self.received_messages = []
        
    async def handle_private_message(self, update, context):
        """处理收到的私信并模拟转发"""
        try:
            user = update.effective_user
            message = update.message
            chat_id = update.effective_chat.id
            
            # 获取用户信息
            user_name = user.first_name or user.username or f"用户{user.id}"
            username = user.username or "无用户名"
            user_id = user.id
            
            # 获取消息内容
            message_text = message.text or ""
            message_time = message.date.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            print(f"\n📨 收到私信:")
            print(f"   用户: {user_name} (@{username})")
            print(f"   ID: {user_id}")
            print(f"   Chat ID: {chat_id}")
            print(f"   消息: {message_text}")
            print(f"   时间: {message_time}")
            
            # 模拟转发给管理员的消息格式
            forward_message = f"""📨 <b>收到私信</b>

👤 <b>用户信息:</b>
• 姓名: {_escape_html(user_name)}
• 用户名: @{username}
• 用户ID: {user_id}
• Chat ID: {chat_id}

📝 <b>消息内容:</b>
{_escape_html(message_text)}

🕒 <b>发送时间:</b> {message_time}

💬 <b>回复方式:</b> 可直接回复此消息或使用 Chat ID: {chat_id}"""
            
            print(f"\n📤 转发给管理员的消息格式:")
            print("-" * 50)
            # 显示HTML格式
            print("HTML格式:")
            print(forward_message)
            print()
            # 显示纯文本格式
            print("纯文本预览:")
            plain_text = forward_message.replace('<b>', '').replace('</b>', '')
            print(plain_text)
            print("-" * 50)
            
            # 记录消息
            self.received_messages.append({
                'user_name': user_name,
                'username': username,
                'user_id': user_id,
                'chat_id': chat_id,
                'message': message_text,
                'time': message_time
            })
            
            # 发送确认消息给用户
            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ 您的消息已收到并转发给管理员"
            )
            
        except Exception as e:
            print(f"❌ 处理私信时发生错误: {e}")

async def test_message_forwarding():
    """测试私信转发功能"""
    print("🧪 测试私信转发功能")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过")
        
        # 检查管理员配置
        admin_chat_id = Config.ADMIN_CHAT_ID
        if not admin_chat_id:
            print("❌ ADMIN_CHAT_ID 未配置")
            return False
        
        print(f"✅ 管理员 Chat ID: {admin_chat_id}")
        
        # 创建测试器
        tester = MessageForwardingTester()
        
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
        print(f"1. 私聊机器人发送任意消息")
        print(f"2. 程序会显示转发给管理员的消息格式")
        print(f"3. 按 Ctrl+C 停止测试")
        print(f"\n⏳ 等待私信消息...")
        
        # 启动机器人
        await application.run_polling()
        
    except KeyboardInterrupt:
        print(f"\n⏹️  测试已停止")
        
        if tester.received_messages:
            print(f"\n📊 测试统计:")
            print(f"   收到私信数量: {len(tester.received_messages)}")
            print(f"\n📋 消息列表:")
            for i, msg in enumerate(tester.received_messages, 1):
                print(f"   {i}. {msg['user_name']} (@{msg['username']}): {msg['message'][:30]}...")
        else:
            print(f"\n⚠️  没有收到任何私信")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_direct_forwarding():
    """测试直接转发功能"""
    print("📤 测试直接转发到管理员")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        admin_chat_id = Config.ADMIN_CHAT_ID
        
        if not admin_chat_id:
            print("❌ ADMIN_CHAT_ID 未配置")
            return False
        
        # 创建机器人应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化机器人
        await application.initialize()
        await application.start()
        
        print(f"✅ 机器人已连接")
        
        # 模拟转发消息
        test_forward_message = f"""📨 <b>收到私信</b>

👤 <b>用户信息:</b>
• 姓名: 测试用户
• 用户名: @testuser
• 用户ID: 123456789
• Chat ID: 987654321

📝 <b>消息内容:</b>
这是一条测试私信消息，用于验证转发功能。

🕒 <b>发送时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

💬 <b>回复方式:</b> 可直接回复此消息或使用 Chat ID: 987654321

<i>📝 这是一条测试消息</i>"""
        
        print(f"\n📤 发送测试转发消息到管理员...")
        
        try:
            await application.bot.send_message(
                chat_id=admin_chat_id,
                text=test_forward_message,
                parse_mode='HTML'
            )
            print(f"✅ 测试转发消息发送成功")
            print(f"📱 请检查管理员是否收到消息")
            
        except Exception as e:
            print(f"❌ 发送转发消息失败: {e}")
            return False
        
        # 停止机器人
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def explain_forwarding_feature():
    """解释转发功能"""
    print("📋 私信转发功能说明")
    print("=" * 50)
    
    print("🔄 工作原理:")
    print("1. 监听所有发送给机器人的私信")
    print("2. 提取用户信息和消息内容")
    print("3. 格式化转发消息")
    print("4. 发送给配置的管理员")
    
    print(f"\n📨 转发内容:")
    print("• 用户姓名和用户名")
    print("• 用户ID和Chat ID")
    print("• 完整的消息内容")
    print("• 消息发送时间")
    print("• 回复方式说明")
    
    print(f"\n🎯 应用场景:")
    print("• 客服支持：及时了解用户需求")
    print("• 问题反馈：收集用户反馈")
    print("• 业务咨询：处理业务相关询问")
    print("• 安全监控：监控可疑私信")
    
    print(f"\n💡 管理员回复:")
    print("• 可以直接使用用户的Chat ID回复")
    print("• 或者通过其他方式联系用户")
    print("• 转发消息包含所有必要信息")

async def main():
    """主函数"""
    print("🧪 私信转发功能测试")
    print("=" * 50)
    
    try:
        # 解释功能
        explain_forwarding_feature()
        
        print("\n" + "=" * 50)
        
        # 询问测试方式
        print(f"\n❓ 选择测试方式:")
        print(f"1. 实时测试 - 启动机器人接收私信")
        print(f"2. 直接测试 - 发送测试转发消息给管理员")
        print(f"3. 跳过测试")
        
        try:
            choice = input("请选择 (1/2/3): ").strip()
            
            if choice == "1":
                print(f"\n🚀 启动实时测试...")
                success = await test_message_forwarding()
            elif choice == "2":
                print(f"\n📤 执行直接测试...")
                success = await test_direct_forwarding()
            else:
                print(f"\n⏭️  跳过测试")
                success = True
            
            if success:
                print(f"\n🎉 测试完成！")
                print(f"\n📋 部署建议:")
                print(f"1. 更新VPS上的main.py文件")
                print(f"2. 确保ADMIN_CHAT_ID已配置")
                print(f"3. 重启TeleLuX服务")
                print(f"4. 测试私聊机器人功能")
                print(f"5. 检查管理员是否收到转发消息")
            
        except KeyboardInterrupt:
            print(f"\n⏹️  测试已取消")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
