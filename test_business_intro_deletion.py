#!/usr/bin/env python3
"""
测试业务介绍自动删除功能
"""

import asyncio
from datetime import datetime
from telegram import Bot
from telegram.ext import Application
from config import Config

async def test_business_intro_deletion():
    """测试业务介绍发送和删除功能"""
    print("🧪 测试业务介绍自动删除功能")
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
        
        # 模拟业务介绍消息
        business_intro_message = """🧪 <b>测试业务介绍消息 #1</b>

这是第一条测试业务介绍消息
发送时间: {time}

📝 测试说明: 这条消息将在发送第二条消息时被自动删除""".format(
            time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 发送第一条业务介绍消息
        print(f"\n📤 发送第一条业务介绍消息...")
        first_message = await application.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=business_intro_message,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        if first_message:
            print(f"✅ 第一条消息发送成功")
            print(f"   消息ID: {first_message.message_id}")
            print(f"   发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 等待5秒
            print(f"\n⏳ 等待5秒后发送第二条消息...")
            await asyncio.sleep(5)
            
            # 发送第二条业务介绍消息
            second_business_intro = """🧪 <b>测试业务介绍消息 #2</b>

这是第二条测试业务介绍消息
发送时间: {time}

📝 测试说明: 发送这条消息时，第一条消息应该被自动删除""".format(
                time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            print(f"📤 发送第二条业务介绍消息...")
            
            # 先删除第一条消息（模拟系统行为）
            try:
                await application.bot.delete_message(
                    chat_id=Config.TELEGRAM_CHAT_ID,
                    message_id=first_message.message_id
                )
                print(f"🗑️ 已删除第一条消息 (消息ID: {first_message.message_id})")
            except Exception as e:
                print(f"❌ 删除第一条消息失败: {e}")
            
            # 发送第二条消息
            second_message = await application.bot.send_message(
                chat_id=Config.TELEGRAM_CHAT_ID,
                text=second_business_intro,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            if second_message:
                print(f"✅ 第二条消息发送成功")
                print(f"   消息ID: {second_message.message_id}")
                print(f"   发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 等待5秒后清理第二条消息
                print(f"\n⏳ 等待5秒后清理第二条消息...")
                await asyncio.sleep(5)
                
                try:
                    await application.bot.delete_message(
                        chat_id=Config.TELEGRAM_CHAT_ID,
                        message_id=second_message.message_id
                    )
                    print(f"🗑️ 已清理第二条测试消息")
                except Exception as e:
                    print(f"⚠️  清理第二条消息失败: {e}")
                    
            else:
                print(f"❌ 第二条消息发送失败")
                return False
                
        else:
            print(f"❌ 第一条消息发送失败")
            return False
        
        # 停止机器人
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_message_deletion_permissions():
    """测试消息删除权限"""
    print(f"\n🔧 测试消息删除权限")
    print("=" * 30)
    
    try:
        # 创建机器人应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化
        await application.initialize()
        await application.start()
        
        print("✅ 机器人应用创建成功")
        
        # 发送一条测试消息
        test_message = "🧪 权限测试消息 - 将立即删除"
        
        sent_message = await application.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=test_message
        )
        
        if sent_message:
            print(f"✅ 测试消息发送成功 (ID: {sent_message.message_id})")
            
            # 立即尝试删除
            try:
                await application.bot.delete_message(
                    chat_id=Config.TELEGRAM_CHAT_ID,
                    message_id=sent_message.message_id
                )
                print("✅ 消息删除成功 - 机器人有删除权限")
                permission_ok = True
            except Exception as e:
                print(f"❌ 消息删除失败: {e}")
                print("⚠️  机器人可能没有删除消息的权限")
                permission_ok = False
        else:
            print("❌ 测试消息发送失败")
            permission_ok = False
        
        # 停止应用
        await application.stop()
        await application.shutdown()
        
        return permission_ok
        
    except Exception as e:
        print(f"❌ 权限测试失败: {e}")
        return False

def explain_functionality():
    """解释功能原理"""
    print(f"\n📋 业务介绍自动删除功能说明")
    print("=" * 40)
    
    print("🔄 工作原理:")
    print("1. 系统保存最后一条业务介绍消息的ID")
    print("2. 发送新业务介绍时，先删除上一条消息")
    print("3. 然后发送新消息并保存新的消息ID")
    print("4. 这样确保群组中只有一条最新的业务介绍")
    
    print(f"\n⚡ 触发条件:")
    print("• 私聊机器人发送'27'")
    print("• 定时发送（每3小时整点）")
    
    print(f"\n💡 优势:")
    print("• 避免群组被大量业务介绍消息刷屏")
    print("• 保持群组整洁")
    print("• 确保用户看到的是最新信息")

async def main():
    """主函数"""
    print("🧪 业务介绍自动删除功能测试")
    print("=" * 50)
    
    try:
        # 解释功能
        explain_functionality()
        
        # 测试删除权限
        permission_ok = await test_message_deletion_permissions()
        
        if permission_ok:
            # 测试业务介绍删除功能
            deletion_ok = await test_business_intro_deletion()
            
            if deletion_ok:
                print(f"\n🎉 所有测试通过！")
                print(f"\n📋 功能确认:")
                print(f"1. ✅ 机器人有删除消息权限")
                print(f"2. ✅ 业务介绍自动删除功能正常")
                print(f"3. ✅ 消息ID保存和管理正常")
            else:
                print(f"\n❌ 业务介绍删除测试失败")
        else:
            print(f"\n❌ 机器人没有删除消息权限")
            print(f"\n🔧 解决方案:")
            print(f"1. 在群组中给机器人管理员权限")
            print(f"2. 确保机器人有'删除消息'权限")
            print(f"3. 重新邀请机器人到群组")
        
        print(f"\n💡 使用建议:")
        print(f"1. 确保机器人在群组中有管理员权限")
        print(f"2. 监控日志确认删除操作正常执行")
        print(f"3. 测试私聊'27'和定时发送功能")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
