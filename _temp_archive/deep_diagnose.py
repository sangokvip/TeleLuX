#!/usr/bin/env python3
"""
深度诊断脚本 - 彻底检查Twitter API问题
"""

import tweepy
import requests
import json
from datetime import datetime, timezone
from config import Config

def test_user_tweets_detailed():
    """详细测试用户推文获取"""
    print("🔍 详细测试推文获取...")
    print("=" * 60)
    
    try:
        # 创建客户端
        client = tweepy.Client(
            bearer_token=Config.TWITTER_BEARER_TOKEN,
            wait_on_rate_limit=True
        )
        
        # 获取用户信息
        print(f"1. 获取用户信息: @{Config.TWITTER_USERNAME}")
        user = client.get_user(
            username=Config.TWITTER_USERNAME,
            user_fields=['public_metrics', 'created_at', 'description', 'protected']
        )
        
        if not user.data:
            print("❌ 无法获取用户信息")
            return False
            
        print(f"✅ 用户信息:")
        print(f"   用户ID: {user.data.id}")
        print(f"   用户名: @{user.data.username}")
        print(f"   显示名: {user.data.name}")
        print(f"   是否受保护: {getattr(user.data, 'protected', 'Unknown')}")
        print(f"   推文数量: {user.data.public_metrics.get('tweet_count', 'Unknown')}")
        print(f"   关注者数: {user.data.public_metrics.get('followers_count', 'Unknown')}")
        
        user_id = user.data.id
        
        # 测试不同的推文获取方法
        print(f"\n2. 测试推文获取 (方法1: 基本获取)")
        try:
            tweets1 = client.get_users_tweets(
                id=user_id,
                max_results=10,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                exclude=['retweets', 'replies']
            )
            
            if tweets1.data:
                print(f"✅ 方法1成功: 获取到 {len(tweets1.data)} 条推文")
                for i, tweet in enumerate(tweets1.data[:3], 1):
                    print(f"   推文{i}: {tweet.text[:50]}... (ID: {tweet.id})")
            else:
                print("❌ 方法1失败: 没有获取到推文数据")
                print(f"   响应元数据: {tweets1.meta if hasattr(tweets1, 'meta') else 'None'}")
                
        except Exception as e:
            print(f"❌ 方法1异常: {e}")
        
        # 方法2: 不排除任何内容
        print(f"\n3. 测试推文获取 (方法2: 包含所有类型)")
        try:
            tweets2 = client.get_users_tweets(
                id=user_id,
                max_results=10,
                tweet_fields=['created_at', 'public_metrics', 'referenced_tweets']
            )
            
            if tweets2.data:
                print(f"✅ 方法2成功: 获取到 {len(tweets2.data)} 条推文")
                for i, tweet in enumerate(tweets2.data[:3], 1):
                    tweet_type = "原创"
                    if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                        ref_type = tweet.referenced_tweets[0].type
                        if ref_type == 'retweeted':
                            tweet_type = "转推"
                        elif ref_type == 'replied_to':
                            tweet_type = "回复"
                    print(f"   推文{i} ({tweet_type}): {tweet.text[:50]}... (ID: {tweet.id})")
            else:
                print("❌ 方法2失败: 没有获取到推文数据")
                
        except Exception as e:
            print(f"❌ 方法2异常: {e}")
        
        # 方法3: 使用原始API
        print(f"\n4. 测试推文获取 (方法3: 原始API)")
        try:
            headers = {
                'Authorization': f'Bearer {Config.TWITTER_BEARER_TOKEN}',
                'User-Agent': 'TeleLuX/1.0'
            }
            
            api_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                'max_results': 10,
                'tweet.fields': 'created_at,public_metrics',
                'exclude': 'retweets,replies'
            }
            
            response = requests.get(api_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    tweets = data['data']
                    print(f"✅ 方法3成功: 获取到 {len(tweets)} 条推文")
                    for i, tweet in enumerate(tweets[:3], 1):
                        print(f"   推文{i}: {tweet['text'][:50]}... (ID: {tweet['id']})")
                        print(f"           时间: {tweet['created_at']}")
                else:
                    print("❌ 方法3失败: API返回空数据")
                    print(f"   完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 方法3失败: HTTP {response.status_code}")
                print(f"   响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 方法3异常: {e}")
        
        # 检查时间线
        print(f"\n5. 检查用户时间线活动")
        try:
            # 获取用户最近的活动（包括转推和回复）
            timeline = client.get_users_tweets(
                id=user_id,
                max_results=20,
                tweet_fields=['created_at', 'referenced_tweets', 'public_metrics']
            )
            
            if timeline.data:
                print(f"✅ 时间线检查: 找到 {len(timeline.data)} 条活动")
                
                original_tweets = []
                retweets = []
                replies = []
                
                for tweet in timeline.data:
                    if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                        ref_type = tweet.referenced_tweets[0].type
                        if ref_type == 'retweeted':
                            retweets.append(tweet)
                        elif ref_type == 'replied_to':
                            replies.append(tweet)
                    else:
                        original_tweets.append(tweet)
                
                print(f"   原创推文: {len(original_tweets)} 条")
                print(f"   转推: {len(retweets)} 条")
                print(f"   回复: {len(replies)} 条")
                
                if original_tweets:
                    latest = original_tweets[0]
                    print(f"   最新原创推文: {latest.text[:100]}...")
                    print(f"   发布时间: {latest.created_at}")
                else:
                    print("   ⚠️  没有找到原创推文，只有转推和回复")
                    
            else:
                print("❌ 时间线检查失败: 没有找到任何活动")
                
        except Exception as e:
            print(f"❌ 时间线检查异常: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 详细测试失败: {e}")
        return False

def check_account_status():
    """检查账号状态"""
    print(f"\n6. 检查账号状态")
    
    try:
        # 手动检查账号是否存在问题
        headers = {
            'Authorization': f'Bearer {Config.TWITTER_BEARER_TOKEN}',
            'User-Agent': 'TeleLuX/1.0'
        }
        
        # 获取用户详细信息
        user_url = f"https://api.twitter.com/2/users/by/username/{Config.TWITTER_USERNAME}"
        params = {
            'user.fields': 'created_at,description,public_metrics,protected,verified'
        }
        
        response = requests.get(user_url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                user_info = data['data']
                print(f"✅ 账号状态检查:")
                print(f"   账号创建时间: {user_info.get('created_at', 'Unknown')}")
                print(f"   是否受保护: {user_info.get('protected', False)}")
                print(f"   是否认证: {user_info.get('verified', False)}")
                print(f"   推文总数: {user_info.get('public_metrics', {}).get('tweet_count', 'Unknown')}")
                
                # 检查是否是受保护账号
                if user_info.get('protected', False):
                    print("⚠️  这是一个受保护的账号！")
                    print("   受保护账号的推文无法通过API获取")
                    print("   这可能是问题的根本原因")
                    return False
                    
        else:
            print(f"❌ 账号状态检查失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 账号状态检查异常: {e}")
    
    return True

def main():
    """主函数"""
    print("🔬 Twitter API 深度诊断")
    print("=" * 60)
    
    try:
        Config.validate()
        print(f"✅ 配置验证通过")
        print(f"   监控用户: @{Config.TWITTER_USERNAME}")
        print(f"   Bearer Token: {Config.TWITTER_BEARER_TOKEN[:20]}...")
        
        # 检查账号状态
        if not check_account_status():
            print("\n❌ 发现账号问题，请检查上述信息")
            return
        
        # 详细测试推文获取
        if test_user_tweets_detailed():
            print(f"\n🎉 诊断完成")
        else:
            print(f"\n❌ 诊断发现问题")
            
        print(f"\n📋 建议:")
        print(f"1. 如果是受保护账号，需要用户授权才能获取推文")
        print(f"2. 如果没有原创推文，只有转推/回复，需要调整过滤条件")
        print(f"3. 检查Bearer Token是否有足够权限")
        print(f"4. 考虑联系Twitter支持检查账号状态")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")

if __name__ == "__main__":
    main()
