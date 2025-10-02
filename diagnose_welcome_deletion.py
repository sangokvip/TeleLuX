#!/usr/bin/env python3
"""
诊断欢迎消息自动删除功能
"""

import asyncio
from datetime import datetime
from telegram.ext import Application, ChatMemberHandler
from config import Config

async def test_job_queue():
    """测试JobQueue功能"""
    print("🔧 测试JobQueue功能")
    print("=" * 50)
    
    try:
        # 创建应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化
        await application.initialize()
        await application.start()
        
        print("✅ 应用已启动")
        
        # 检查JobQueue是否可用
        if application.job_queue:
            print("✅ JobQueue可用")
            
            # 测试简单的定时任务
            test_executed = False
            
            async def test_job(context):
                nonlocal test_executed
                test_executed = True
                print("✅ 测试任务执行成功")
            
            # 安排5秒后执行
            application.job_queue.run_once(test_job, when=5)
            print("⏰ 已安排5秒后执行测试任务...")
            
            # 等待任务执行
            await asyncio.sleep(6)
            
            if test_executed:
                print("🎉 JobQueue功能正常")
                result = True
            else:
                print("❌ JobQueue任务未执行")
                result = False
        else:
            print("❌ JobQueue不可用")
            result = False
        
        # 停止应用
        await application.stop()
        await application.shutdown()
        
        return result
        
    except Exception as e:
        print(f"❌ JobQueue测试失败: {e}")
        return False

async def test_message_deletion():
    """测试消息删除功能"""
    print("🗑️ 测试消息删除功能")
    print("=" * 50)
    
    try:
        # 创建应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化
        await application.initialize()
        await application.start()
        
        print("✅ 应用已启动")
        
        # 发送测试消息
        test_message = "🧪 测试消息 - 将在10秒后删除"
        
        sent_message = await application.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=test_message
        )
        
        if sent_message:
            print(f"✅ 测试消息发送成功 (ID: {sent_message.message_id})")
            
            # 等待10秒
            print("⏳ 等待10秒后删除消息...")
            await asyncio.sleep(10)
            
            # 尝试删除消息
            try:
                await application.bot.delete_message(
                    chat_id=Config.TELEGRAM_CHAT_ID,
                    message_id=sent_message.message_id
                )
                print("✅ 消息删除成功")
                result = True
            except Exception as e:
                print(f"❌ 消息删除失败: {e}")
                result = False
        else:
            print("❌ 测试消息发送失败")
            result = False
        
        # 停止应用
        await application.stop()
        await application.shutdown()
        
        return result
        
    except Exception as e:
        print(f"❌ 消息删除测试失败: {e}")
        return False

async def test_combined_functionality():
    """测试组合功能：发送消息并使用JobQueue删除"""
    print("🔄 测试组合功能")
    print("=" * 50)
    
    try:
        # 创建应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化
        await application.initialize()
        await application.start()
        
        print("✅ 应用已启动")
        
        # 发送测试消息
        test_message = "🧪 组合测试消息 - 将通过JobQueue在15秒后删除"
        
        sent_message = await application.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=test_message
        )
        
        if sent_message:
            print(f"✅ 测试消息发送成功 (ID: {sent_message.message_id})")
            
            # 使用JobQueue安排删除
            deletion_executed = False
            
            async def delete_message_job(context):
                nonlocal deletion_executed
                try:
                    await context.bot.delete_message(
                        chat_id=Config.TELEGRAM_CHAT_ID,
                        message_id=sent_message.message_id
                    )
                    deletion_executed = True
                    print("✅ JobQueue删除消息成功")
                except Exception as e:
                    print(f"❌ JobQueue删除消息失败: {e}")
            
            # 安排15秒后删除
            application.job_queue.run_once(delete_message_job, when=15)
            print("⏰ 已安排15秒后通过JobQueue删除消息...")
            
            # 等待删除执行
            await asyncio.sleep(16)
            
            if deletion_executed:
                print("🎉 组合功能正常")
                result = True
            else:
                print("❌ JobQueue删除未执行")
                result = False
        else:
            print("❌ 测试消息发送失败")
            result = False
        
        # 停止应用
        await application.stop()
        await application.shutdown()
        
        return result
        
    except Exception as e:
        print(f"❌ 组合功能测试失败: {e}")
        return False

def check_bot_permissions():
    """检查机器人权限"""
    print("🔒 检查机器人权限")
    print("=" * 50)
    
    print("📋 机器人需要的权限:")
    print("1. 发送消息权限")
    print("2. 删除消息权限")
    print("3. 管理员权限（推荐）")
    print()
    print("⚠️  如果机器人没有删除消息权限，自动删除功能将无法工作")
    print("💡 解决方案：在群组中给机器人管理员权限")

async def main():
    """主函数"""
    print("🧪 欢迎消息自动删除功能诊断")
    print("=" * 50)
    
    try:
        # 验证必要的Telegram配置
        Config.require_telegram(require_chat_id=True)
        print("✅ 配置验证通过")
        print(f"📱 群组ID: {Config.TELEGRAM_CHAT_ID}")
        
        # 检查权限
        check_bot_permissions()
        
        print("\n" + "=" * 50)
        
        # 测试JobQueue
        print("\n🔧 步骤1: 测试JobQueue功能")
        job_queue_ok = await test_job_queue()
        
        if not job_queue_ok:
            print("❌ JobQueue功能异常，自动删除无法工作")
            return
        
        print("\n" + "=" * 50)
        
        # 测试消息删除
        print("\n🗑️ 步骤2: 测试消息删除功能")
        deletion_ok = await test_message_deletion()
        
        if not deletion_ok:
            print("❌ 消息删除功能异常，可能是权限问题")
            print("💡 请确保机器人在群组中有管理员权限")
            return
        
        print("\n" + "=" * 50)
        
        # 测试组合功能
        print("\n🔄 步骤3: 测试组合功能")
        combined_ok = await test_combined_functionality()
        
        if combined_ok:
            print("\n🎉 所有测试通过！")
            print("\n📋 诊断结果:")
            print("1. ✅ JobQueue功能正常")
            print("2. ✅ 消息删除功能正常")
            print("3. ✅ 组合功能正常")
            print("\n💡 欢迎消息自动删除功能应该能正常工作")
            print("\n🔧 如果仍然不工作，可能的原因:")
            print("• 系统重启导致JobQueue任务丢失")
            print("• 8小时太长，难以观察到效果")
            print("• 日志中可能有相关错误信息")
        else:
            print("\n❌ 组合功能测试失败")
            print("\n🔧 可能的问题:")
            print("• 机器人权限不足")
            print("• JobQueue配置问题")
            print("• 网络连接问题")
        
        print(f"\n📋 建议:")
        print(f"1. 确保机器人在群组中有管理员权限")
        print(f"2. 检查系统日志: sudo journalctl -u telex.service -f")
        print(f"3. 观察欢迎消息是否在8小时后被删除")
        print(f"4. 如需快速测试，可临时修改删除时间为几分钟")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
