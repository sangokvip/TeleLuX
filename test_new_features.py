#!/usr/bin/env python3
"""
测试新功能：
1. 私信"clear"清除欢迎消息
2. 用户超过1次进群/退群才通知管理员
"""

import asyncio
from datetime import datetime
from telegram.ext import Application
from config import Config

async def test_clear_command():
    """测试clear命令功能"""
    print("🧪 测试clear命令功能")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        admin_chat_id = Config.ADMIN_CHAT_ID
        
        if not admin_chat_id:
            print("❌ ADMIN_CHAT_ID 未配置")
            return False
        
        print(f"✅ 管理员 Chat ID: {admin_chat_id}")
        
        # 创建应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化
        await application.initialize()
        await application.start()
        
        print("✅ 机器人已连接")
        
        # 发送测试说明给管理员
        test_message = f"""🧪 <b>Clear命令功能测试</b>

📋 <b>测试步骤:</b>
1. 私聊机器人发送 <code>clear</code>
2. 观察群内欢迎消息是否被清除
3. 检查是否收到清除结果通知

💡 <b>功能说明:</b>
• 私聊发送 'clear' 可清除群内所有欢迎消息
• 清除后会收到详细的统计报告
• 支持批量清除，安全可靠

⚠️ <b>注意:</b>
• 只有存在的欢迎消息才会被清除
• 已被手动删除的消息会自动跳过
• 清除操作会记录详细日志

🎯 <b>测试方法:</b>
请私聊机器人发送: clear

⏰ <b>测试时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        await application.bot.send_message(
            chat_id=admin_chat_id,
            text=test_message,
            parse_mode='HTML'
        )
        
        print("✅ 测试说明已发送给管理员")
        
        # 停止应用
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_user_activity_notification():
    """测试用户活动通知功能"""
    print("🧪 测试用户活动通知功能")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        admin_chat_id = Config.ADMIN_CHAT_ID
        
        # 创建应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化
        await application.initialize()
        await application.start()
        
        print("✅ 机器人已连接")
        
        # 发送测试说明给管理员
        test_message = f"""🧪 <b>用户活动通知功能测试</b>

📋 <b>功能变更:</b>
• <b>之前:</b> 用户每次进群/退群都通知管理员
• <b>现在:</b> 只有超过1次进群/退群才通知管理员

🎯 <b>通知条件:</b>
• 用户第2次及以后进群 → 发送通知
• 用户第2次及以后退群 → 发送通知
• 首次进群/退群 → 不发送通知

💡 <b>优势:</b>
• 减少无意义的通知
• 专注于可疑的重复行为
• 提高管理效率

📊 <b>测试方法:</b>
1. 邀请测试用户加入群组（第1次 - 无通知）
2. 让测试用户离开群组（第1次 - 无通知）
3. 再次邀请用户加入（第2次 - 有通知）
4. 再次让用户离开（第2次 - 有通知）

⏰ <b>测试时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ <b>功能已启用，可以开始测试</b>"""
        
        await application.bot.send_message(
            chat_id=admin_chat_id,
            text=test_message,
            parse_mode='HTML'
        )
        
        print("✅ 测试说明已发送给管理员")
        
        # 停止应用
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def send_feature_summary():
    """发送功能总结"""
    print("📋 发送功能总结")
    print("=" * 30)
    
    try:
        # 验证配置
        Config.validate()
        admin_chat_id = Config.ADMIN_CHAT_ID
        
        # 创建应用
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 初始化
        await application.initialize()
        await application.start()
        
        # 发送功能总结
        summary_message = f"""🎉 <b>TeleLuX新功能上线</b>

🆕 <b>功能1: 私信清除欢迎消息</b>
• 命令: 私聊发送 <code>clear</code>
• 功能: 立即清除群内所有欢迎消息
• 反馈: 清除完成后发送统计报告

🆕 <b>功能2: 智能活动通知</b>
• 优化: 只有重复进群/退群才通知
• 条件: 超过1次进群或退群
• 效果: 减少无意义通知，专注可疑行为

📊 <b>完整功能列表:</b>
• 自动欢迎新用户 (1分钟后自动删除)
• 定时业务介绍 (每3小时整点)
• Twitter推文分享功能
• 智能用户活动监控 ⭐<b>已优化</b>
• 私信消息转发给管理员
• 一键回复系统
• 欢迎消息批量清除 ⭐<b>新增</b>

💡 <b>私聊命令:</b>
• <code>27</code> - 发送业务介绍
• <code>clear</code> - 清除欢迎消息 ⭐<b>新增</b>
• Twitter URL - 分享推文

🚀 <b>系统状态:</b> 所有功能已就绪

⏰ <b>更新时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        await application.bot.send_message(
            chat_id=admin_chat_id,
            text=summary_message,
            parse_mode='HTML'
        )
        
        print("✅ 功能总结已发送")
        
        # 停止应用
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

def explain_new_features():
    """解释新功能"""
    print("📋 新功能说明")
    print("=" * 50)
    
    print("🆕 功能1: 私信'clear'清除欢迎消息")
    print("• 触发方式: 私聊机器人发送 'clear'")
    print("• 功能效果: 立即清除群内所有欢迎消息")
    print("• 反馈机制: 发送详细的清除统计报告")
    print("• 安全性: 自动跳过已删除的消息")
    
    print(f"\n🆕 功能2: 智能用户活动通知")
    print("• 优化逻辑: 只有重复行为才通知")
    print("• 通知条件: 超过1次进群或退群")
    print("• 减少干扰: 避免首次进群的无意义通知")
    print("• 专注重点: 识别可疑的重复进退群行为")
    
    print(f"\n🎯 使用场景:")
    print("• Clear命令: 群组消息过多时快速清理")
    print("• 智能通知: 专注监控可疑用户行为")
    print("• 提高效率: 减少无关通知，专注重要信息")

async def main():
    """主函数"""
    print("🧪 TeleLuX新功能测试")
    print("=" * 50)
    
    try:
        # 解释新功能
        explain_new_features()
        
        print("\n" + "=" * 50)
        
        # 询问测试选项
        print(f"\n❓ 选择测试功能:")
        print(f"1. 测试clear命令功能")
        print(f"2. 测试用户活动通知功能")
        print(f"3. 发送功能总结")
        print(f"4. 发送所有测试内容")
        print(f"5. 跳过测试")
        
        try:
            choice = input("请选择 (1/2/3/4/5): ").strip()
            
            if choice == "1":
                print(f"\n🧪 测试clear命令功能...")
                success = await test_clear_command()
                
            elif choice == "2":
                print(f"\n🧪 测试用户活动通知功能...")
                success = await test_user_activity_notification()
                
            elif choice == "3":
                print(f"\n📋 发送功能总结...")
                success = await send_feature_summary()
                
            elif choice == "4":
                print(f"\n📤 发送所有测试内容...")
                success1 = await test_clear_command()
                await asyncio.sleep(2)
                success2 = await test_user_activity_notification()
                await asyncio.sleep(2)
                success3 = await send_feature_summary()
                success = success1 and success2 and success3
                
            else:
                print(f"\n⏭️  跳过测试")
                success = True
            
            if success:
                print(f"\n🎉 测试完成！")
                print(f"\n📋 下一步:")
                print(f"1. 测试clear命令: 私聊机器人发送 'clear'")
                print(f"2. 测试用户活动: 邀请用户多次进退群")
                print(f"3. 确认功能正常后部署到生产环境")
                
                print(f"\n🚀 部署步骤:")
                print(f"1. 更新VPS上的main.py文件")
                print(f"2. 重启TeleLuX服务")
                print(f"3. 测试新功能")
                print(f"4. 监控日志确认正常运行")
            else:
                print(f"\n❌ 测试失败")
        
        except KeyboardInterrupt:
            print(f"\n⏹️  测试已取消")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
