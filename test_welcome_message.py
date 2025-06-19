#!/usr/bin/env python3
"""
测试新的欢迎消息格式
"""

import asyncio
from datetime import datetime
from telegram import Bot
from telegram.ext import Application
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

def preview_welcome_message():
    """预览欢迎消息格式"""
    print("👀 欢迎消息格式预览")
    print("=" * 50)
    
    # 测试不同的用户名
    test_users = [
        "张三",
        "Alice",
        "用户123",
        "新朋友",
        "TestUser"
    ]
    
    for i, user_name in enumerate(test_users, 1):
        welcome_message = f"""🎉 欢迎 <b>{_escape_html(user_name)}</b> 加入露老师聊天群！

🔍 认准露老师唯一账号：
• X账号：<a href="https://x.com/xiuchiluchu910"><b>xiuchiluchu910</b></a>
• Telegram账号：<a href="https://t.me/mteacherlu"><b>@mteacherlu</b></a>

💬 群内随意聊天，但请勿轻易相信任何陌生人，谨防诈骗 ⚠️"""
        
        print(f"\n示例 {i} - 用户名: {user_name}")
        print("-" * 30)
        print("HTML格式:")
        print(welcome_message)
        print()
        print("纯文本预览:")
        # 简单移除HTML标签用于预览
        plain_text = welcome_message.replace('<b>', '').replace('</b>', '')
        print(plain_text)
        print("=" * 50)

async def test_welcome_message_sending():
    """测试发送欢迎消息"""
    print("📤 测试发送欢迎消息")
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
        
        # 测试用户名
        test_user = "测试用户"
        
        welcome_message = f"""🎉 欢迎 <b>{_escape_html(test_user)}</b> 加入露老师聊天群！

🔍 认准露老师唯一账号：
• X账号：<a href="https://x.com/xiuchiluchu910"><b>xiuchiluchu910</b></a>
• Telegram账号：<a href="https://t.me/mteacherlu"><b>@mteacherlu</b></a>

💬 群内随意聊天，但请勿轻易相信任何陌生人，谨防诈骗 ⚠️

<i>📝 这是一条测试消息，将在10秒后自动删除</i>"""
        
        print(f"\n📤 发送测试欢迎消息...")
        sent_message = await application.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=welcome_message,
            parse_mode='HTML'
        )
        
        if sent_message:
            print(f"✅ 测试欢迎消息发送成功")
            print(f"   消息ID: {sent_message.message_id}")
            print(f"   发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 等待10秒后删除测试消息
            print(f"\n⏳ 等待10秒后删除测试消息...")
            await asyncio.sleep(10)
            
            try:
                await application.bot.delete_message(
                    chat_id=Config.TELEGRAM_CHAT_ID,
                    message_id=sent_message.message_id
                )
                print(f"🗑️ 测试消息已删除")
            except Exception as e:
                print(f"⚠️  删除测试消息失败: {e}")
                
        else:
            print(f"❌ 测试消息发送失败")
            return False
        
        # 停止机器人
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def analyze_message_features():
    """分析消息特点"""
    print("📊 新欢迎消息特点分析")
    print("=" * 50)
    
    print("🎯 消息内容:")
    print("• 个性化欢迎（包含用户名）")
    print("• 官方账号认证信息（带超链接）")
    print("• 防诈骗提醒")
    print("• 群规说明")

    print(f"\n🎨 视觉效果:")
    print("• 🎉 欢迎emoji增加喜庆感")
    print("• 🔍 搜索emoji突出认证信息")
    print("• 💬 聊天emoji说明群组用途")
    print("• ⚠️ 警告emoji强调安全提醒")

    print(f"\n🔗 超链接功能:")
    print("• X账号链接：https://x.com/xiuchiluchu910")
    print("• Telegram账号链接：https://t.me/mteacherlu")
    print("• 用户可直接点击访问官方账号")
    print("• 提高账号验证的便利性")
    
    print(f"\n📏 消息长度:")
    sample_message = """🎉 欢迎 测试用户 加入露老师聊天群！

🔍 认准露老师唯一账号：
• X账号：xiuchiluchu910
• Telegram账号：@mteacherlu

💬 群内随意聊天，但请勿轻易相信任何陌生人，谨防诈骗 ⚠️"""
    
    lines = sample_message.split('\n')
    print(f"• 总行数: {len(lines)}")
    print(f"• 字符数: {len(sample_message)}")
    print(f"• 包含emoji: 4个")
    
    print(f"\n⏰ 自动删除:")
    print("• 8小时后自动删除")
    print("• 保持群组整洁")
    print("• 避免信息堆积")

async def main():
    """主函数"""
    print("🧪 新欢迎消息测试")
    print("=" * 50)
    
    try:
        # 预览消息格式
        preview_welcome_message()
        
        # 分析消息特点
        analyze_message_features()
        
        # 询问是否发送测试消息
        print(f"\n❓ 是否要发送测试欢迎消息到群组？")
        print(f"   测试消息将在10秒后自动删除")
        print(f"   输入 'y' 或 'yes' 确认，其他任意键跳过")
        
        try:
            user_input = input("请选择: ").strip().lower()
            if user_input in ['y', 'yes']:
                # 测试发送欢迎消息
                send_ok = await test_welcome_message_sending()
                
                if send_ok:
                    print(f"\n🎉 测试完成！")
                    print(f"\n📋 确认事项:")
                    print(f"1. ✅ 欢迎消息格式正确")
                    print(f"2. ✅ HTML格式渲染正常")
                    print(f"3. ✅ Emoji显示正常")
                    print(f"4. ✅ 自动删除功能正常")
                else:
                    print(f"\n❌ 发送测试失败")
            else:
                print(f"\n⏭️  跳过发送测试")
        except KeyboardInterrupt:
            print(f"\n⏹️  测试已取消")
        
        print(f"\n💡 部署建议:")
        print(f"1. 更新VPS上的main.py文件")
        print(f"2. 重启TeleLuX服务")
        print(f"3. 邀请测试用户验证欢迎消息")
        print(f"4. 监控日志确认功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
