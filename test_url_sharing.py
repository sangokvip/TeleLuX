#!/usr/bin/env python3
"""
测试Twitter URL分享功能
"""

import tweepy
import re
from config import Config

def test_url_parsing():
    """测试URL解析功能"""
    print("🔍 测试URL解析功能")
    print("=" * 50)
    
    # 测试URL列表
    test_urls = [
        "https://twitter.com/elonmusk/status/1234567890123456789",
        "https://x.com/elonmusk/status/1234567890123456789",
        "twitter.com/elonmusk/status/1234567890123456789",
        "x.com/elonmusk/status/1234567890123456789",
        "https://www.twitter.com/elonmusk/status/1234567890123456789",
        "https://www.x.com/elonmusk/status/1234567890123456789",
        "请看这个推文 https://twitter.com/elonmusk/status/1234567890123456789 很有趣",
        "不是推文链接 https://google.com",
        "https://twitter.com/elonmusk",  # 不是推文链接
    ]
    
    def is_twitter_url(text):
        """检查文本是否包含Twitter URL"""
        twitter_patterns = [
            r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
            r'https?://(?:www\.)?x\.com/\w+/status/\d+',
            r'twitter\.com/\w+/status/\d+',
            r'x\.com/\w+/status/\d+'
        ]
        
        for pattern in twitter_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def extract_tweet_id(url):
        """从Twitter URL中提取推文ID"""
        patterns = [
            r'(?:twitter|x)\.com/\w+/status/(\d+)',
            r'/status/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    print("测试URL识别和ID提取:")
    for i, url in enumerate(test_urls, 1):
        is_valid = is_twitter_url(url)
        tweet_id = extract_tweet_id(url) if is_valid else None
        
        print(f"{i:2d}. {url}")
        print(f"    是否为推文URL: {'✅' if is_valid else '❌'}")
        if tweet_id:
            print(f"    提取的推文ID: {tweet_id}")
        print()

def test_tweet_fetching():
    """测试推文获取功能"""
    print("🐦 测试推文获取功能")
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
        
        # 测试推文ID（使用一个公开的推文）
        test_tweet_ids = [
            "1234567890123456789",  # 示例ID，可能不存在
            "1",  # 第一条推文（可能存在）
        ]
        
        print("测试推文获取:")
        for tweet_id in test_tweet_ids:
            print(f"\n测试推文ID: {tweet_id}")
            
            try:
                tweet = client.get_tweet(
                    id=tweet_id,
                    tweet_fields=['created_at', 'public_metrics', 'author_id'],
                    user_fields=['username', 'name'],
                    expansions=['author_id']
                )
                
                if tweet.data:
                    print("✅ 推文获取成功")
                    print(f"   内容: {tweet.data.text[:100]}...")
                    print(f"   时间: {tweet.data.created_at}")
                    print(f"   作者ID: {tweet.data.author_id}")
                    
                    # 获取作者信息
                    if tweet.includes and 'users' in tweet.includes:
                        for user in tweet.includes['users']:
                            if user.id == tweet.data.author_id:
                                print(f"   作者: @{user.username}")
                                break
                else:
                    print("❌ 推文数据为空")
                    
            except tweepy.NotFound:
                print("❌ 推文不存在或已被删除")
            except tweepy.Unauthorized:
                print("❌ 无权访问该推文")
            except Exception as e:
                print(f"❌ 获取失败: {e}")
        
        # 测试获取一个真实存在的推文（Twitter官方账号的推文）
        print(f"\n测试获取Twitter官方账号的推文:")
        try:
            # 先获取Twitter官方账号的最新推文
            twitter_user = client.get_user(username="twitter")
            if twitter_user.data:
                user_tweets = client.get_users_tweets(
                    id=twitter_user.data.id,
                    max_results=5,
                    tweet_fields=['created_at', 'author_id'],
                    exclude=['retweets', 'replies']
                )
                
                if user_tweets.data:
                    latest_tweet = user_tweets.data[0]
                    print(f"✅ 找到真实推文ID: {latest_tweet.id}")
                    
                    # 测试获取这个真实推文
                    real_tweet = client.get_tweet(
                        id=latest_tweet.id,
                        tweet_fields=['created_at', 'public_metrics', 'author_id'],
                        user_fields=['username', 'name'],
                        expansions=['author_id']
                    )
                    
                    if real_tweet.data:
                        print("✅ 真实推文获取成功")
                        print(f"   内容: {real_tweet.data.text[:100]}...")
                        print(f"   时间: {real_tweet.data.created_at}")
                        
                        # 构造URL
                        url = f"https://twitter.com/twitter/status/{real_tweet.data.id}"
                        print(f"   URL: {url}")
                        
                        return True
                        
        except Exception as e:
            print(f"❌ 获取真实推文失败: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 Twitter URL分享功能测试")
    print("=" * 50)
    
    try:
        # 测试URL解析
        test_url_parsing()
        
        print("\n" + "=" * 50)
        
        # 测试推文获取
        if test_tweet_fetching():
            print("\n🎉 所有测试通过！")
            print("\n📋 使用说明:")
            print("1. 私聊机器人发送Twitter URL")
            print("2. 机器人会自动分享该推文到群组")
            print("3. 支持twitter.com和x.com域名")
        else:
            print("\n⚠️  部分测试失败，但URL解析功能正常")
            
        print("\n💡 测试建议:")
        print("1. 找一个真实的Twitter URL进行测试")
        print("2. 确保推文是公开的，不是私密账号")
        print("3. 检查Bearer Token权限")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
