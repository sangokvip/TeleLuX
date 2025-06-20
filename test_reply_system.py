#!/usr/bin/env python3
"""
测试一键回复系统
"""

import asyncio
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from config import Config

class ReplySystemTester:
    def __init__(self):
        self.admin_chat_id = Config.ADMIN_CHAT_ID
        
    async def simulate_private_message_forward(self, context):
        """模拟私信转发（带回复按钮）"""
        try:
            # 模拟用户信息
            test_user_id = "123456789"
            test_user_name = "测试用户"
            test_username = "testuser"
            test_message = "您好，我想了解VIP群组的详细信息"
            test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # 构建转发消息
            forward_message = f"""📨 <b>收到私信</b>

👤 <b>用户信息:</b>
• 姓名: {test_user_name}
• 用户名: @{test_username}
• 用户ID: {test_user_id}
• Chat ID: {test_user_id}

📝 <b>消息内容:</b>
{test_message}

🕒 <b>发送时间:</b> {test_time}"""

            # 创建回复按钮
            keyboard = [
                [
                    InlineKeyboardButton("💬 快速回复", callback_data=f"reply_{test_user_id}"),
                    InlineKeyboardButton("📋 复制Chat ID", callback_data=f"copy_{test_user_id}")
                ],
                [
                    InlineKeyboardButton("🚫 忽略", callback_data=f"ignore_{test_user_id}"),
                    InlineKeyboardButton("⚠️ 标记可疑", callback_data=f"suspicious_{test_user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # 发送测试消息给管理员
            await context.bot.send_message(
                chat_id=self.admin_chat_id,
                text=forward_message,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            print(f"✅ 已发送测试私信转发消息给管理员")
            print(f"📱 管理员可以点击按钮测试回复功能")
            
        except Exception as e:
            print(f"❌ 发送测试消息失败: {e}")

    async def handle_callback_query(self, update, context):
        """处理回调查询（用于测试）"""
        try:
            query = update.callback_query
            await query.answer()
            
            callback_data = query.data
            action, target_chat_id = callback_data.split('_', 1)
            
            print(f"📨 收到回调查询: {action} for {target_chat_id}")
            
            if action == "reply":
                reply_message = f"""💬 <b>回复用户消息</b>

🎯 <b>目标用户 Chat ID:</b> {target_chat_id}

📝 <b>请发送您要回复的消息内容</b>
格式：/reply {target_chat_id} 您的回复内容

💡 <b>示例:</b>
/reply {target_chat_id} 您好，感谢您的咨询！VIP群组详情如下...

⚠️ <b>注意:</b> 请确保消息内容准确，发送后无法撤回"""
                
                await query.edit_message_text(
                    text=reply_message,
                    parse_mode='HTML'
                )
                print("✅ 快速回复按钮测试成功")
                
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
                print("✅ 复制Chat ID按钮测试成功")
                
            elif action == "ignore":
                ignore_message = f"""🚫 <b>消息已标记为忽略</b>

👤 <b>用户 Chat ID:</b> {target_chat_id}
⏰ <b>操作时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 此消息已被标记为已处理"""
                
                await query.edit_message_text(
                    text=ignore_message,
                    parse_mode='HTML'
                )
                print("✅ 忽略按钮测试成功")
                
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
                print("✅ 标记可疑按钮测试成功")
                
        except Exception as e:
            print(f"❌ 处理回调查询失败: {e}")

    async def handle_reply_command(self, update, context):
        """处理回复命令（用于测试）"""
        try:
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
            
            print(f"📨 收到回复命令: 目标 {target_chat_id}, 内容: {reply_content}")
            
            # 模拟发送回复（实际环境中会发送给真实用户）
            print(f"📤 模拟发送回复给用户 {target_chat_id}: {reply_content}")
            
            # 确认消息
            confirm_message = f"""✅ <b>回复已发送（测试模式）</b>

🎯 <b>目标用户:</b> {target_chat_id}
📝 <b>回复内容:</b> {reply_content}
⏰ <b>发送时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 在实际环境中，此消息将发送给用户"""
            
            await update.message.reply_text(
                text=confirm_message,
                parse_mode='HTML'
            )
            
            print("✅ 回复命令测试成功")
            
        except Exception as e:
            print(f"❌ 处理回复命令失败: {e}")

async def test_reply_system():
    """测试回复系统"""
    print("🧪 测试一键回复系统")
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
        tester = ReplySystemTester()
        
        # 创建应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 添加处理器
        callback_handler = CallbackQueryHandler(tester.handle_callback_query)
        application.add_handler(callback_handler)
        
        reply_handler = MessageHandler(filters.Regex(r'^/reply\s+'), tester.handle_reply_command)
        application.add_handler(reply_handler)
        
        # 初始化
        await application.initialize()
        await application.start()
        
        print("✅ 机器人已启动")
        
        # 发送测试消息
        print("\n📤 发送测试私信转发消息...")
        await tester.simulate_private_message_forward(application)
        
        print("\n📋 测试说明:")
        print("1. 管理员会收到带按钮的私信转发消息")
        print("2. 点击'💬 快速回复'按钮获取回复指令")
        print("3. 使用 /reply [Chat_ID] [消息] 命令回复")
        print("4. 点击其他按钮测试相应功能")
        print("5. 按 Ctrl+C 停止测试")
        
        print("\n⏳ 等待管理员操作...")
        
        # 启动机器人
        await application.run_polling()
        
    except KeyboardInterrupt:
        print(f"\n⏹️  测试已停止")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def explain_reply_system():
    """解释回复系统功能"""
    print("📋 一键回复系统说明")
    print("=" * 50)
    
    print("🎯 解决的问题:")
    print("• 用户没有用户名时难以回复")
    print("• 需要手动复制Chat ID")
    print("• 回复操作繁琐")
    print("• 缺乏消息管理功能")
    
    print(f"\n🔧 系统功能:")
    print("• 💬 快速回复：获取回复命令格式")
    print("• 📋 复制Chat ID：方便复制用户ID")
    print("• 🚫 忽略：标记消息已处理")
    print("• ⚠️ 标记可疑：记录可疑用户")
    
    print(f"\n📱 使用流程:")
    print("1. 用户发送私信给机器人")
    print("2. 机器人转发消息给管理员（带按钮）")
    print("3. 管理员点击'快速回复'按钮")
    print("4. 按照提示使用 /reply 命令回复")
    print("5. 消息自动发送给用户")
    
    print(f"\n💡 命令格式:")
    print("/reply [Chat_ID] [消息内容]")
    print("示例：/reply 123456789 您好，感谢您的咨询！")

async def main():
    """主函数"""
    print("🧪 一键回复系统测试")
    print("=" * 50)
    
    try:
        # 解释系统功能
        explain_reply_system()
        
        print("\n" + "=" * 50)
        
        # 询问是否开始测试
        print(f"\n❓ 是否开始测试一键回复系统？")
        print(f"   测试将发送带按钮的消息给管理员")
        print(f"   输入 'y' 或 'yes' 确认，其他任意键跳过")
        
        try:
            choice = input("请选择: ").strip().lower()
            if choice in ['y', 'yes']:
                success = await test_reply_system()
                
                if success:
                    print(f"\n🎉 测试完成！")
                    print(f"\n📋 部署建议:")
                    print(f"1. 更新VPS上的main.py文件")
                    print(f"2. 重启TeleLuX服务")
                    print(f"3. 测试私聊机器人功能")
                    print(f"4. 验证管理员收到带按钮的转发消息")
                    print(f"5. 测试回复命令功能")
            else:
                print(f"\n⏭️  跳过测试")
        except KeyboardInterrupt:
            print(f"\n⏹️  测试已取消")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
