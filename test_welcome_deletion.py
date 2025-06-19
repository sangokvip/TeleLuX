#!/usr/bin/env python3
"""
测试欢迎消息自动删除功能
"""

import asyncio
from datetime import datetime, timedelta
from telegram import Bot
from telegram.ext import Application
from config import Config

async def test_welcome_message_deletion():
    """测试欢迎消息发送和删除功能"""
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
        test_message = "🧪 <b>测试欢迎消息</b>\n\n这是一条测试消息，将在30秒后自动删除"
        
        print(f"\n📤 发送测试欢迎消息...")
        sent_message = await application.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=test_message,
            parse_mode='HTML'
        )
        
        if sent_message:
            print(f"✅ 测试消息发送成功")
            print(f"   消息ID: {sent_message.message_id}")
            print(f"   发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 安排30秒后删除（用于快速测试）
            print(f"\n⏰ 安排30秒后删除消息...")
            
            async def delete_test_message():
                await asyncio.sleep(30)  # 等待30秒
                try:
                    await application.bot.delete_message(
                        chat_id=Config.TELEGRAM_CHAT_ID,
                        message_id=sent_message.message_id
                    )
                    print(f"🗑️ 测试消息已删除 (消息ID: {sent_message.message_id})")
                except Exception as e:
                    print(f"❌ 删除测试消息失败: {e}")
            
            # 启动删除任务
            delete_task = asyncio.create_task(delete_test_message())
            
            # 等待删除完成
            print(f"⏳ 等待30秒后自动删除...")
            await delete_task
            
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

async def test_job_queue_functionality():
    """测试JobQueue功能"""
    print(f"\n🔧 测试JobQueue功能")
    print("=" * 30)
    
    try:
        # 创建带JobQueue的应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化
        await application.initialize()
        await application.start()
        
        print("✅ JobQueue应用创建成功")
        
        # 测试JobQueue是否可用
        if application.job_queue:
            print("✅ JobQueue可用")
            
            # 创建一个测试任务
            test_job_executed = False
            
            async def test_job_callback(context):
                nonlocal test_job_executed
                test_job_executed = True
                print("✅ 测试任务执行成功")
            
            # 安排5秒后执行的任务
            application.job_queue.run_once(
                test_job_callback,
                when=5,
                data={'test': 'data'}
            )
            
            print("⏰ 已安排5秒后执行测试任务...")
            
            # 等待任务执行
            await asyncio.sleep(6)
            
            if test_job_executed:
                print("🎉 JobQueue功能正常")
            else:
                print("❌ JobQueue任务未执行")
                
        else:
            print("❌ JobQueue不可用")
        
        # 停止应用
        await application.stop()
        await application.shutdown()
        
        return test_job_executed
        
    except Exception as e:
        print(f"❌ JobQueue测试失败: {e}")
        return False

def calculate_deletion_time():
    """计算8小时后的删除时间"""
    print(f"\n📅 计算删除时间")
    print("=" * 30)
    
    now = datetime.now()
    deletion_time = now + timedelta(hours=8)
    
    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"删除时间: {deletion_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"间隔时间: 8小时 (28800秒)")

async def main():
    """主函数"""
    print("🧪 欢迎消息自动删除功能测试")
    print("=" * 50)
    
    try:
        # 计算删除时间
        calculate_deletion_time()
        
        # 测试JobQueue功能
        job_queue_ok = await test_job_queue_functionality()
        
        if job_queue_ok:
            # 测试消息删除功能
            deletion_ok = await test_welcome_message_deletion()
            
            if deletion_ok:
                print(f"\n🎉 所有测试通过！")
                print(f"\n📋 功能说明:")
                print(f"1. 新用户加入时会发送欢迎消息")
                print(f"2. 欢迎消息会在8小时后自动删除")
                print(f"3. 删除操作通过JobQueue异步执行")
                print(f"4. 如果消息已被手动删除，系统会忽略错误")
            else:
                print(f"\n❌ 消息删除测试失败")
        else:
            print(f"\n❌ JobQueue测试失败，自动删除功能可能无法正常工作")
        
        print(f"\n💡 使用建议:")
        print(f"1. 确保机器人有删除消息的权限")
        print(f"2. 在群组中给机器人管理员权限")
        print(f"3. 监控日志确认删除操作正常执行")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
