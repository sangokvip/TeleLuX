#!/usr/bin/env python3
"""
测试用户进群退群监控功能
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

def simulate_user_activity():
    """模拟用户活动数据"""
    print("🧪 模拟用户活动监控功能")
    print("=" * 50)
    
    # 模拟用户活动日志
    user_activity_log = {}
    
    # 模拟用户1：多次进群退群
    user_id_1 = 123456789
    user_activity_log[user_id_1] = {
        'user_name': '测试用户A',
        'username': 'testuser_a',
        'join_times': [
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 2, 14, 30, 0),
            datetime(2024, 1, 3, 16, 15, 0)
        ],
        'leave_times': [
            datetime(2024, 1, 1, 12, 0, 0),
            datetime(2024, 1, 2, 18, 0, 0)
        ],
        'total_joins': 3,
        'total_leaves': 2
    }
    
    # 模拟用户2：正常用户
    user_id_2 = 987654321
    user_activity_log[user_id_2] = {
        'user_name': '正常用户B',
        'username': 'normaluser_b',
        'join_times': [
            datetime(2024, 1, 1, 9, 0, 0)
        ],
        'leave_times': [],
        'total_joins': 1,
        'total_leaves': 0
    }
    
    # 生成通知消息
    for user_id, user_data in user_activity_log.items():
        if user_data['total_joins'] > 1 or user_data['total_leaves'] > 0:
            print(f"\n📨 用户 {user_data['user_name']} 的活动通知:")
            print("-" * 40)
            
            # 构建活动历史
            all_activities = []
            for join_time in user_data['join_times']:
                all_activities.append(('加入', join_time))
            for leave_time in user_data['leave_times']:
                all_activities.append(('离开', leave_time))
            
            # 按时间排序
            all_activities.sort(key=lambda x: x[1])
            
            # 格式化活动历史
            activity_history = []
            for activity_type, activity_time in all_activities:
                time_str = activity_time.strftime('%Y-%m-%d %H:%M:%S')
                activity_history.append(f"• {activity_type}: {time_str}")
            
            # 构建通知消息
            notification_message = f"""🚨 用户活动监控

👤 用户信息:
• 姓名: {user_data['user_name']}
• 用户名: @{user_data['username']}
• ID: {user_id}

📊 活动统计:
• 总加入次数: {user_data['total_joins']}
• 总离开次数: {user_data['total_leaves']}

📝 活动历史:
{chr(10).join(activity_history)}

⚠️ 该用户存在多次进群/退群行为，请注意关注。"""
            
            print(notification_message)
            print("=" * 50)

async def test_notification_sending():
    """测试发送通知功能"""
    print("📤 测试发送通知到 bryansuperb")
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
        
        # 模拟通知消息
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

<i>📝 这是一条测试消息</i>"""
        
        print(f"\n📤 发送测试通知到 bryansuperb...")
        
        try:
            await application.bot.send_message(
                chat_id="bryansuperb",
                text=test_notification,
                parse_mode='HTML'
            )
            print(f"✅ 测试通知发送成功")
            
        except Exception as e:
            print(f"❌ 发送通知失败: {e}")
            print(f"💡 可能的原因:")
            print(f"   1. bryansuperb 没有与机器人开始对话")
            print(f"   2. 用户名不存在或已更改")
            print(f"   3. 机器人被用户屏蔽")
            return False
        
        # 停止机器人
        await application.stop()
        await application.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def explain_monitoring_system():
    """解释监控系统工作原理"""
    print("📋 用户活动监控系统说明")
    print("=" * 50)
    
    print("🔄 工作原理:")
    print("1. 监听群组成员状态变化事件")
    print("2. 记录每个用户的加入和离开时间")
    print("3. 统计用户的总加入和离开次数")
    print("4. 检测到重复进群/退群行为时发送通知")
    
    print(f"\n📊 监控数据:")
    print("• 用户ID、姓名、用户名")
    print("• 每次加入的具体时间")
    print("• 每次离开的具体时间")
    print("• 总加入次数和总离开次数")
    
    print(f"\n🚨 触发条件:")
    print("• 用户第2次及以上加入群组")
    print("• 用户离开群组（如果之前加入过）")
    
    print(f"\n📨 通知内容:")
    print("• 用户基本信息（姓名、用户名、ID）")
    print("• 活动统计（总加入次数、总离开次数）")
    print("• 完整的活动历史时间线")
    print("• 当前触发的动作（加入/离开）")
    
    print(f"\n🎯 应用场景:")
    print("• 识别可疑的频繁进退群行为")
    print("• 监控潜在的恶意用户")
    print("• 帮助管理员了解群组活动")
    print("• 提供用户行为分析数据")

async def main():
    """主函数"""
    print("🧪 用户进群退群监控功能测试")
    print("=" * 50)
    
    try:
        # 解释监控系统
        explain_monitoring_system()
        
        print("\n" + "=" * 50)
        
        # 模拟用户活动
        simulate_user_activity()
        
        print("\n" + "=" * 50)
        
        # 询问是否发送测试通知
        print(f"\n❓ 是否要发送测试通知到 bryansuperb？")
        print(f"   注意：bryansuperb 需要先与机器人开始对话")
        print(f"   输入 'y' 或 'yes' 确认，其他任意键跳过")
        
        try:
            user_input = input("请选择: ").strip().lower()
            if user_input in ['y', 'yes']:
                # 测试发送通知
                send_ok = await test_notification_sending()
                
                if send_ok:
                    print(f"\n🎉 测试完成！")
                    print(f"\n📋 确认事项:")
                    print(f"1. ✅ 通知消息格式正确")
                    print(f"2. ✅ 发送到 bryansuperb 成功")
                    print(f"3. ✅ HTML格式渲染正常")
                else:
                    print(f"\n❌ 发送测试失败")
                    print(f"\n🔧 解决方案:")
                    print(f"1. 让 bryansuperb 先与机器人私聊发送 /start")
                    print(f"2. 确认用户名 bryansuperb 正确")
                    print(f"3. 检查机器人Token权限")
            else:
                print(f"\n⏭️  跳过发送测试")
        except KeyboardInterrupt:
            print(f"\n⏹️  测试已取消")
        
        print(f"\n💡 部署建议:")
        print(f"1. 更新VPS上的main.py文件")
        print(f"2. 重启TeleLuX服务")
        print(f"3. 让 bryansuperb 与机器人开始对话")
        print(f"4. 测试用户进群退群行为")
        print(f"5. 监控日志确认功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
