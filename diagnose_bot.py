#!/usr/bin/env python3
"""
机器人功能测试脚本 - 本地诊断测试
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_config():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    try:
        from config import Config
        
        # 测试配置验证
        try:
            Config.validate()
            print("配置验证通过")
        except ValueError as e:
            print(f"配置验证失败: {e}")
            return False
        
        # 检查关键配置
        print(f"机器人Token: {Config.TELEGRAM_BOT_TOKEN[:10]}..." if Config.TELEGRAM_BOT_TOKEN else "机器人Token为空")
        print(f"聊天ID: {Config.TELEGRAM_CHAT_ID}")
        print(f"Twitter用户名: {Config.TWITTER_USERNAME}")
        print(f"检查间隔: {Config.CHECK_INTERVAL}秒")
        
        return True
    except Exception as e:
        print(f"配置测试失败: {e}")
        traceback.print_exc()
        return False

async def test_database():
    """测试数据库连接"""
    print("\n=== 测试数据库连接 ===")
    try:
        from database import Database
        
        db = Database()
        
        # 测试数据库基本操作
        test_tweet_id = "test_1234567890"
        
        # 检查推文是否已处理
        is_processed = db.is_tweet_processed(test_tweet_id)
        print(f"测试推文处理状态: {'已处理' if is_processed else '未处理'}")
        
        # 测试黑名单功能
        test_user_id = 123456789
        is_blacklisted = db.is_user_blacklisted(test_user_id)
        print(f"测试用户黑名单状态: {'在黑名单中' if is_blacklisted else '不在黑名单中'}")
        
        # 获取统计数据
        processed_count = db.get_processed_tweets_count()
        blacklist_count = db.get_blacklist_count()
        print(f"已处理推文数量: {processed_count}")
        print(f"黑名单用户数量: {blacklist_count}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        traceback.print_exc()
        return False

async def test_twitter_monitor():
    """测试Twitter监控功能"""
    print("\n=== 测试Twitter监控功能 ===")
    try:
        from twitter_monitor import TwitterMonitor
        from config import Config
        
        monitor = TwitterMonitor()
        
        # 测试API连接
        print("正在测试Twitter API连接...")
        if monitor.test_connection():
            print("✅ Twitter API连接成功")
        else:
            print("❌ Twitter API连接失败")
            return False
        
        # 测试获取用户信息
        username = Config.TWITTER_USERNAME
        if username:
            print(f"正在获取 @{username} 的用户信息...")
            user_id = monitor.get_user_id(username)
            if user_id:
                print(f"✅ 获取用户ID成功: {user_id}")
                
                # 测试获取最新推文
                print(f"正在获取 @{username} 的最新推文...")
                tweets = monitor.get_latest_tweets(username, count=1)
                if tweets:
                    tweet = tweets[0]
                    print(f"✅ 获取推文成功:")
                    print(f"  推文ID: {tweet['id']}")
                    print(f"  内容: {tweet['text'][:100]}...")
                    print(f"  时间: {tweet['created_at']}")
                    print(f"  URL: {tweet['url']}")
                else:
                    print("⚠️  未获取到推文（可能是账号私密或无最新推文）")
            else:
                print(f"❌ 无法获取用户 @{username} 的ID")
        else:
            print("⚠️  未配置Twitter用户名")
        
        return True
    except Exception as e:
        print(f"❌ Twitter监控测试失败: {e}")
        traceback.print_exc()
        return False

async def test_message_handling():
    """测试消息处理逻辑（模拟）"""
    print("\n=== 测试消息处理逻辑 ===")
    try:
        from main import TeleLuXBot
        from utils import utils
        
        bot = TeleLuXBot()
        
        # 测试工具函数
        print("正在测试工具函数...")
        
        # 测试HTML转义
        test_html = '<script>alert("test")</script>&test'
        escaped = utils.escape_html(test_html)
        print(f"HTML转义测试: {escaped}")
        
        # 测试Twitter URL检查
        test_url = "https://twitter.com/user/status/1234567890"
        is_twitter = utils.is_twitter_url(test_url)
        print(f"Twitter URL检查: {is_twitter}")
        
        # 测试推文ID提取
        tweet_id = utils.extract_tweet_id(test_url)
        print(f"推文ID提取: {tweet_id}")
        
        # 测试内存管理器
        print("正在测试内存管理器...")
        bot.user_activity_manager.add("test_user_123", {
            'user_name': '测试用户',
            'total_joins': 1,
            'total_leaves': 0
        })
        
        user_data = bot.user_activity_manager.get("test_user_123")
        if user_data:
            print(f"✅ 内存管理器测试成功: {user_data['user_name']}")
        else:
            print("❌ 内存管理器测试失败")
        
        return True
    except Exception as e:
        print(f"❌ 消息处理测试失败: {e}")
        traceback.print_exc()
        return False

async def test_bot_integration():
    """测试机器人整体集成"""
    print("\n=== 测试机器人整体集成 ===")
    try:
        from main import TeleLuXBot
        from config import Config
        
        # 创建机器人实例
        bot = TeleLuXBot()
        
        # 初始化组件
        print("正在初始化机器人组件...")
        
        # 初始化数据库
        from database import Database
        bot.database = Database()
        print("✅ 数据库初始化完成")
        
        # 初始化Twitter监控
        from twitter_monitor import TwitterMonitor
        bot.twitter_monitor = TwitterMonitor()
        print("✅ Twitter监控初始化完成")
        
        # 测试关键方法
        print("正在测试关键方法...")
        
        # 测试Twitter URL识别
        test_message = "Check this tweet: https://twitter.com/user/status/1234567890"
        is_twitter = bot._is_twitter_url(test_message)
        print(f"Twitter URL识别测试: {is_twitter}")
        
        # 测试推文ID提取
        tweet_id = bot._extract_tweet_id(test_message)
        print(f"推文ID提取测试: {tweet_id}")
        
        # 测试HTML转义
        test_text = "测试<script>alert('xss')</script>文本"
        escaped = bot._escape_html(test_text)
        print(f"HTML转义测试: {escaped}")
        
        print("✅ 机器人集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 机器人集成测试失败: {e}")
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("开始机器人功能诊断测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("配置加载", await test_config()))
    test_results.append(("数据库连接", await test_database()))
    test_results.append(("Twitter监控", await test_twitter_monitor()))
    test_results.append(("消息处理逻辑", await test_message_handling()))
    test_results.append(("机器人集成", await test_bot_integration()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 诊断测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("所有测试通过！机器人功能正常")
        print("\n如果机器人在VPS上不工作，请检查:")
        print("1. 环境变量是否正确设置")
        print("2. 网络连接是否正常")
        print("3. 防火墙设置是否允许出站连接")
        print("4. Telegram Bot Token是否有效")
        print("5. Twitter API Token是否有效")
        return 0
    else:
        print("部分测试失败，请检查错误信息")
        print("\n建议:")
        print("1. 检查日志文件获取详细错误信息")
        print("2. 验证所有API密钥和令牌")
        print("3. 确保所有依赖包已正确安装")
        print("4. 检查VPS服务器的网络配置")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)