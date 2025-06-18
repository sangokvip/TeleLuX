#!/usr/bin/env python3
"""
测试时间范围推文获取功能
"""

import tweepy
from datetime import datetime, timezone, timedelta
from config import Config

def test_time_range_tweets():
    """测试时间范围推文获取"""
    print("🕒 测试时间范围推文获取功能")
    print("=" * 50)
    
    try:
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过")
        
        # 创建客户端
        client = tweepy.Client(
            bearer_token=Config.TWITTER_BEARER_TOKEN,
            wait_on_rate_limit=True
        )
        
        # 获取用户信息
        username = Config.TWITTER_USERNAME
        print(f"\n👤 获取用户信息: @{username}")
        user = client.get_user(username=username)
        
        if not user.data:
            print("❌ 无法获取用户信息")
            return False
        
        user_id = user.data.id
        print(f"✅ 用户ID: {user_id}")
        
        # 设置时间范围（过去一周）
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=7)
        
        print(f"\n🕒 时间范围:")
        print(f"   开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # 测试1: 使用时间范围查询
        print(f"\n📊 测试1: 使用时间范围查询")
        try:
            tweets = client.get_users_tweets(
                id=user_id,
                max_results=10,
                tweet_fields=['created_at', 'public_metrics', 'referenced_tweets'],
                start_time=start_time,
                end_time=end_time,
                exclude=['retweets', 'replies']
            )
            
            if tweets.data:
                print(f"✅ 获取到 {len(tweets.data)} 条推文")
                
                # 显示推文信息
                for i, tweet in enumerate(tweets.data[:3], 1):
                    tweet_time = tweet.created_at
                    time_str = tweet_time.strftime('%Y-%m-%d %H:%M:%S UTC')
                    print(f"   推文{i}: {tweet.text[:50]}...")
                    print(f"          时间: {time_str}")
                    print(f"          ID: {tweet.id}")
                    
                    # 检查时间是否在范围内
                    if start_time <= tweet_time <= end_time:
                        print(f"          ✅ 时间在范围内")
                    else:
                        print(f"          ❌ 时间超出范围")
                    print()
                    
            else:
                print("❌ 没有获取到推文")
                print("   可能原因:")
                print("   1. 用户在过去一周内没有发布原创推文")
                print("   2. 用户只发布了转推或回复")
                print("   3. 用户账号受保护")
                
        except Exception as e:
            print(f"❌ 时间范围查询失败: {e}")
        
        # 测试2: 不使用时间范围，获取所有推文然后过滤
        print(f"\n📊 测试2: 获取所有推文然后过滤")
        try:
            all_tweets = client.get_users_tweets(
                id=user_id,
                max_results=20,
                tweet_fields=['created_at', 'public_metrics', 'referenced_tweets'],
                exclude=['retweets', 'replies']
            )
            
            if all_tweets.data:
                print(f"✅ 获取到 {len(all_tweets.data)} 条历史推文")
                
                # 过滤时间范围
                recent_tweets = []
                for tweet in all_tweets.data:
                    if start_time <= tweet.created_at <= end_time:
                        recent_tweets.append(tweet)
                
                print(f"✅ 过滤后得到 {len(recent_tweets)} 条一周内的推文")
                
                # 显示最新3条
                for i, tweet in enumerate(recent_tweets[:3], 1):
                    time_str = tweet.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                    print(f"   推文{i}: {tweet.text[:50]}...")
                    print(f"          时间: {time_str}")
                    print()
                    
            else:
                print("❌ 没有获取到历史推文")
                
        except Exception as e:
            print(f"❌ 历史推文查询失败: {e}")
        
        # 测试3: 包含所有类型的推文
        print(f"\n📊 测试3: 包含所有类型推文")
        try:
            all_types = client.get_users_tweets(
                id=user_id,
                max_results=10,
                tweet_fields=['created_at', 'referenced_tweets'],
                start_time=start_time,
                end_time=end_time
                # 不排除任何类型
            )
            
            if all_types.data:
                print(f"✅ 获取到 {len(all_types.data)} 条推文（包含所有类型）")
                
                # 分析推文类型
                original = 0
                retweets = 0
                replies = 0
                
                for tweet in all_types.data:
                    if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                        ref_type = tweet.referenced_tweets[0].type
                        if ref_type == 'retweeted':
                            retweets += 1
                        elif ref_type == 'replied_to':
                            replies += 1
                    else:
                        original += 1
                
                print(f"   原创推文: {original} 条")
                print(f"   转推: {retweets} 条")
                print(f"   回复: {replies} 条")
                
            else:
                print("❌ 没有获取到任何类型的推文")
                
        except Exception as e:
            print(f"❌ 所有类型查询失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 时间范围推文获取测试")
    print("=" * 50)
    
    try:
        if test_time_range_tweets():
            print("\n🎉 测试完成")
        else:
            print("\n❌ 测试失败")
            
        print("\n📋 说明:")
        print("1. 如果没有获取到推文，可能是用户在过去一周内没有发布原创推文")
        print("2. 如果只有转推和回复，说明用户最近没有发布原创内容")
        print("3. 如果完全没有推文，可能是账号受保护或API权限问题")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
