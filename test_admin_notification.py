#!/usr/bin/env python3
"""
测试管理员通知功能
"""

import asyncio
from datetime import datetime
from telegram.ext import Application
from config import Config

async def test_admin_notification():
    """测试发送通知到管理员"""
    print("📤 测试管理员通知功能")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过")
        
        # 检查 ADMIN_CHAT_ID
        admin_chat_id = Config.ADMIN_CHAT_ID
        if not admin_chat_id:
            print("❌ ADMIN_CHAT_ID 未配置")
            print("\n🔧 解决步骤:")
            print("1. 运行: python3 get_chat_id.py")
            print("2. 让 bryansuperb 私聊机器人发送消息")
            print("3. 获取 Chat ID 后添加到 .env 文件")
            print("4. 在 .env 文件中添加: ADMIN_CHAT_ID=获取到的数字")
            return False
        
        print(f"✅ 管理员 Chat ID: {admin_chat_id}")
        
        # 创建机器人应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化机器人
        await application.initialize()
        await application.start()
        
        print(f"✅ 机器人已连接")
        
        # 构建测试通知消息
        test_notification = f"""🧪 <b>用户活动监控测试</b>

👤 <b>用户信息:</b>
• 姓名: 测试用户
• 用户名: @testuser
• ID: 123456789

📊 <b>活动统计:</b>
• 总加入次数: 2
• 总离开次数: 1
• 当前动作: 加入

📝 <b>活动历史:</b>
• 加入: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• 离开: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• 加入: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ 该用户存在多次进群/退群行为，请注意关注。

<i>📝 这是一条测试消息，用于验证通知功能</i>"""
        
        print(f"\n📤 发送测试通知...")
        
        try:
            await application.bot.send_message(
                chat_id=admin_chat_id,
                text=test_notification,
                parse_mode='HTML'
            )
            print(f"✅ 测试通知发送成功")
            print(f"📱 请检查 Chat ID {admin_chat_id} 是否收到消息")
            
        except Exception as e:
            print(f"❌ 发送通知失败: {e}")
            print(f"\n💡 可能的原因:")
            print(f"   1. Chat ID 不正确")
            print(f"   2. 用户没有与机器人开始对话")
            print(f"   3. 机器人被用户屏蔽")
            return False
        
        # 停止机器人
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def check_env_file():
    """检查 .env 文件配置"""
    print("🔍 检查 .env 文件配置")
    print("=" * 30)
    
    try:
        with open('.env', 'r') as f:
            content = f.read()
            
        print("📋 当前 .env 文件内容:")
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                if 'TOKEN' in line or 'ID' in line:
                    # 隐藏敏感信息
                    key, value = line.split('=', 1)
                    if len(value) > 10:
                        masked_value = value[:5] + '*' * (len(value) - 10) + value[-5:]
                    else:
                        masked_value = '*' * len(value)
                    print(f"   {key}={masked_value}")
                else:
                    print(f"   {line}")
        
        # 检查是否有 ADMIN_CHAT_ID
        if 'ADMIN_CHAT_ID=' in content:
            print("\n✅ ADMIN_CHAT_ID 已配置")
        else:
            print("\n❌ ADMIN_CHAT_ID 未配置")
            print("\n🔧 添加步骤:")
            print("1. 编辑 .env 文件: nano .env")
            print("2. 添加一行: ADMIN_CHAT_ID=bryansuperb的Chat_ID")
            print("3. 保存文件")
            
    except FileNotFoundError:
        print("❌ .env 文件不存在")
    except Exception as e:
        print(f"❌ 读取 .env 文件失败: {e}")

async def main():
    """主函数"""
    print("🧪 管理员通知功能测试")
    print("=" * 50)
    
    try:
        # 检查配置文件
        check_env_file()
        
        print("\n" + "=" * 50)
        
        # 测试通知功能
        success = await test_admin_notification()
        
        if success:
            print(f"\n🎉 测试成功！")
            print(f"\n📋 确认事项:")
            print(f"1. ✅ 管理员 Chat ID 配置正确")
            print(f"2. ✅ 通知消息发送成功")
            print(f"3. ✅ HTML格式渲染正常")
            
            print(f"\n📱 下一步:")
            print(f"1. 确认管理员收到测试消息")
            print(f"2. 更新 VPS 上的代码")
            print(f"3. 重启 TeleLuX 服务")
            print(f"4. 测试实际的用户进群退群功能")
        else:
            print(f"\n❌ 测试失败")
            print(f"\n🔧 解决步骤:")
            print(f"1. 确保 bryansuperb 已与机器人开始对话")
            print(f"2. 运行 get_chat_id.py 获取正确的 Chat ID")
            print(f"3. 将 Chat ID 添加到 .env 文件")
            print(f"4. 重新运行此测试")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
