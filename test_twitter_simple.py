#!/usr/bin/env python3
"""
简单的Twitter API测试脚本
使用Tweepy库测试Bearer Token
"""

import tweepy
import sys
from config import Config

def test_twitter_with_tweepy():
    """使用Tweepy测试Twitter API"""
    print("🔍 使用Tweepy测试Twitter API...")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过")
        print(f"   Bearer Token: {Config.TWITTER_BEARER_TOKEN[:20]}...")
        print(f"   监控用户: @{Config.TWITTER_USERNAME}")
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False
    
    try:
        # 创建Tweepy客户端
        print("\n🔗 创建Twitter客户端...")
        client = tweepy.Client(
            bearer_token=Config.TWITTER_BEARER_TOKEN,
            wait_on_rate_limit=True
        )
        print("✅ Twitter客户端创建成功")
        
        # 测试获取用户信息
        print(f"\n👤 测试获取用户信息: @{Config.TWITTER_USERNAME}")
        user = client.get_user(username=Config.TWITTER_USERNAME)
        
        if user.data:
            print("✅ 用户信息获取成功")
            print(f"   用户ID: {user.data.id}")
            print(f"   用户名: @{user.data.username}")
            print(f"   显示名: {user.data.name}")
            
            user_id = user.data.id
            
            # 测试获取推文
            print(f"\n🐦 测试获取推文...")
            tweets = client.get_users_tweets(
                id=user_id,
                max_results=5,
                tweet_fields=['created_at', 'public_metrics'],
                exclude=['retweets', 'replies']
            )
            
            if tweets.data:
                print(f"✅ 推文获取成功，共 {len(tweets.data)} 条")
                
                # 显示最新推文
                latest_tweet = tweets.data[0]
                print(f"\n📝 最新推文:")
                print(f"   ID: {latest_tweet.id}")
                print(f"   内容: {latest_tweet.text[:100]}...")
                print(f"   时间: {latest_tweet.created_at}")
                print(f"   链接: https://twitter.com/{Config.TWITTER_USERNAME}/status/{latest_tweet.id}")
                
                return True
            else:
                print("❌ 没有获取到推文数据")
                return False
                
        else:
            print("❌ 用户信息获取失败")
            return False
            
    except tweepy.Unauthorized as e:
        print(f"❌ Twitter API认证失败: {e}")
        print("💡 请检查Bearer Token是否正确")
        return False
        
    except tweepy.Forbidden as e:
        print(f"❌ Twitter API权限不足: {e}")
        print("💡 可能的原因:")
        print("   1. Bearer Token权限不足")
        print("   2. 账号被限制")
        print("   3. API端点访问受限")
        return False
        
    except tweepy.TooManyRequests as e:
        print(f"❌ Twitter API速率限制: {e}")
        print("💡 请等待15分钟后重试")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        return False

def main():
    """主函数"""
    print("🧪 Twitter API 简单测试")
    print("=" * 50)
    
    try:
        if test_twitter_with_tweepy():
            print("\n🎉 所有测试通过！Twitter API工作正常")
            print("\n📋 建议:")
            print("1. 重启TeleLuX服务: sudo systemctl restart telex.service")
            print("2. 查看服务状态: sudo systemctl status telex.service")
            print("3. 测试功能: 私聊机器人发送'x'")
        else:
            print("\n❌ 测试失败，请检查配置和网络连接")
            print("\n🔧 故障排除:")
            print("1. 检查Bearer Token是否正确")
            print("2. 确认网络连接正常")
            print("3. 验证Twitter用户名正确")
            print("4. 检查Twitter Developer账号状态")
            
    except KeyboardInterrupt:
        print("\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
