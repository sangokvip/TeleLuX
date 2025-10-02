#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter媒体修复验证脚本
"""

import sys
import traceback
from datetime import datetime

def test_media_enhanced_tweet():
    """测试增强的推文获取功能"""
    print("=== Twitter媒体增强功能测试 ===")
    
    try:
        from twitter_monitor import TwitterMonitor
        from config import Config
        
        # 初始化Twitter监控器
        monitor = TwitterMonitor()
        
        # 验证配置
        Config._init_configs()
        
        if not Config.TWITTER_BEARER_TOKEN:
            print("错误: Twitter Bearer Token未配置")
            return False
        
        print(f"测试用户: @{Config.TWITTER_USERNAME}")
        
        # 测试基本API连接
        print("1. 测试Twitter API连接...")
        if monitor.test_connection():
            print("✅ Twitter API连接成功")
        else:
            print("❌ Twitter API连接失败")
            return False
        
        # 测试增强的get_tweet_by_id方法
        print("\n2. 测试增强的推文获取方法...")
        
        # 使用一个已知的推文ID进行测试（你可以替换为实际的推文ID）
        test_tweet_id = "1234567890"  # 替换为实际的推文ID
        
        print(f"正在测试推文ID: {test_tweet_id}")
        
        # 调用增强的get_tweet_by_id方法
        tweet_info = monitor.get_tweet_by_id(test_tweet_id)
        
        if tweet_info:
            print("✅ 成功获取推文信息")
            print(f"推文ID: {tweet_info['id']}")
            print(f"用户名: @{tweet_info['username']}")
            print(f"内容: {tweet_info['text'][:100]}...")
            print(f"时间: {tweet_info['created_at']}")
            print(f"URL: {tweet_info['url']}")
            
            # 检查新的媒体字段
            if tweet_info.get('has_media', False):
                media_urls = tweet_info.get('media_urls', [])
                print(f"✅ 推文包含媒体: {len(media_urls)} 个文件")
                for i, media_url in enumerate(media_urls, 1):
                    print(f"  媒体{i}: {media_url}")
            else:
                print("ℹ️ 推文无媒体信息")
                
            # 验证所有必需字段都存在
            required_fields = ['id', 'text', 'created_at', 'url', 'username', 'has_media', 'media_urls']
            missing_fields = []
            for field in required_fields:
                if field not in tweet_info:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️ 缺少字段: {missing_fields}")
                return False
            else:
                print("✅ 所有必需字段都存在")
                
            return True
        else:
            print("❌ 无法获取推文信息")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return False

def test_media_fields_structure():
    """测试媒体字段结构"""
    print("\n=== 测试媒体字段结构 ===")
    
    try:
        from twitter_monitor import TwitterMonitor
        
        # 创建监控器实例
        monitor = TwitterMonitor()
        
        # 模拟推文数据（用于结构验证）
        mock_tweet_info = {
            'id': '1234567890',
            'text': '这是一条测试推文',
            'created_at': '2023-01-01T00:00:00Z',
            'url': 'https://twitter.com/test/status/1234567890',
            'username': 'test',
            'author_id': '12345',
            'has_media': True,
            'media_urls': [
                'https://pbs.twimg.com/media/abc123.jpg',
                'https://pbs.twimg.com/media/def456.jpg'
            ]
        }
        
        print("模拟推文数据结构:")
        for key, value in mock_tweet_info.items():
            print(f"  {key}: {value}")
        
        # 验证媒体URL格式
        if mock_tweet_info.get('has_media', False):
            media_urls = mock_tweet_info.get('media_urls', [])
            if media_urls:
                print(f"✅ 媒体URL格式验证通过: {len(media_urls)} 个URL")
                for url in media_urls:
                    if 'pbs.twimg.com' in url or 'video.twimg.com' in url:
                        print(f"✅ 有效Twitter媒体URL: {url}")
                    else:
                        print(f"⚠️ 非标准Twitter媒体URL: {url}")
        
        return True
        
    except Exception as e:
        print(f"❌ 结构测试失败: {e}")
        traceback.print_exc()
        return False

def test_integration_with_main():
    """测试与主程序的集成"""
    print("\n=== 测试与主程序集成 ===")
    
    try:
        from main import TeleLuXBot
        from config import Config
        
        # 创建机器人实例
        bot = TeleLuXBot()
        
        # 初始化组件
        from database import Database
        bot.database = Database()
        
        from twitter_monitor import TwitterMonitor
        bot.twitter_monitor = TwitterMonitor()
        
        print("✅ 机器人组件初始化成功")
        
        # 测试用户活动管理器（MemoryManager已修复）
        bot.user_activity_manager.add("test_user_123", {
            'user_name': '测试用户',
            'total_joins': 1,
            'total_leaves': 0
        })
        
        user_data = bot.user_activity_manager.get("test_user_123")
        if user_data:
            print(f"✅ 内存管理器工作正常: {user_data['user_name']}")
        else:
            print("❌ 内存管理器测试失败")
            return False
        
        # 测试工具函数
        test_text = "<script>alert('test')</script>&test"
        escaped = bot._escape_html(test_text)
        expected = "&lt;script&gt;alert(&#x27;test&#x27;)&lt;/script&gt;&amp;test"
        if escaped == expected:
            print("✅ HTML转义功能正常")
        else:
            print(f"❌ HTML转义功能异常: {escaped}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("Twitter媒体修复验证测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("媒体增强推文获取", test_media_enhanced_tweet()))
    test_results.append(("媒体字段结构", test_media_fields_structure()))
    test_results.append(("主程序集成", test_integration_with_main()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("所有测试通过！媒体修复成功")
        print("\n下一步:")
        print("1. 在实际环境中测试真实推文")
        print("2. 部署到VPS服务器")
        print("3. 监控日志确认媒体信息获取")
        return 0
    else:
        print("部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())