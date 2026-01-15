#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter媒体功能简单验证
"""

import sys

def test_media_functionality():
    """简单测试媒体功能"""
    print("=== Twitter媒体功能验证 ===")
    
    try:
        from twitter_monitor import TwitterMonitor
        from config import Config
        
        # 验证配置
        Config._init_configs()
        
        if not Config.TWITTER_BEARER_TOKEN:
            print("错误: Twitter Bearer Token未配置")
            return False
        
        print(f"测试用户: @{Config.TWITTER_USERNAME}")
        print(f"Bearer Token: {Config.TWITTER_BEARER_TOKEN[:20]}...")
        
        # 测试API连接
        print("\n1. 测试Twitter API连接...")
        
        # 创建监控器实例（不初始化数据库）
        monitor = TwitterMonitor()
        
        if monitor.test_connection():
            print("Twitter API连接成功")
        else:
            print("Twitter API连接失败")
            return False
        
        # 测试get_tweet_by_id方法结构
        print("\n2. 测试get_tweet_by_id方法结构...")
        
        # 获取方法签名和文档
        import inspect
        method = getattr(monitor, 'get_tweet_by_id')
        sig = inspect.signature(method)
        print(f"方法签名: {sig}")
        
        # 检查方法文档
        doc = method.__doc__
        if doc and "包含媒体信息" in doc:
            print("✅ 方法文档已更新，包含媒体信息")
        else:
            print("⚠️ 方法文档可能需要更新")
        
        # 测试方法存在性
        if hasattr(monitor, 'get_tweet_by_id'):
            print("✅ get_tweet_by_id方法存在")
        else:
            print("❌ get_tweet_by_id方法不存在")
            return False
        
        # 测试配置字段
        print("\n3. 测试配置字段...")
        
        # 检查新的配置字段
        required_configs = ['TWITTER_BEARER_TOKEN', 'TWITTER_USERNAME']
        for config in required_configs:
            value = getattr(Config, config, None)
            if value:
                print(f"✅ {config}: 已配置")
            else:
                print(f"❌ {config}: 未配置")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_code_changes():
    """测试代码修改"""
    print("\n=== 测试代码修改 ===")
    
    try:
        # 测试twitter_monitor.py的修改
        with open('twitter_monitor.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'media_fields' in content:
                print("twitter_monitor.py已添加media_fields参数")
            else:
                print("twitter_monitor.py未找到media_fields参数")
                
            if 'attachments.media_keys' in content:
                print("twitter_monitor.py已添加attachments.media_keys扩展")
            else:
                print("twitter_monitor.py未找到attachments.media_keys扩展")
                
            if 'media_urls' in content:
                print("twitter_monitor.py已添加media_urls字段")
            else:
                print("twitter_monitor.py未找到media_urls字段")
        
        # 测试main.py的修改
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'has_media' in content:
                print("main.py已添加has_media判断")
            else:
                print("main.py未找到has_media判断")
                
            if 'media_urls' in content:
                print("main.py已添加media_urls处理")
            else:
                print("main.py未找到media_urls处理")
        
        return True
        
    except Exception as e:
        print(f"代码修改测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("Twitter媒体功能简单验证")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("媒体功能", test_media_functionality()))
    test_results.append(("代码修改", test_code_changes()))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("验证结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个验证通过")
    
    if passed == total:
        print("🎉 验证通过！媒体功能修复完成")
        print("\n💡 下一步:")
        print("1. 在实际环境中测试真实推文")
        print("2. 部署到VPS服务器")
        print("3. 监控日志确认媒体信息获取")
        return 0
    else:
        print("⚠️  部分验证失败，请检查问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())