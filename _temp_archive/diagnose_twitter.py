#!/usr/bin/env python3
"""
Twitter API 诊断脚本
用于检查Twitter API连接和推文获取问题
"""

import requests
import json
from datetime import datetime
from config import Config

def test_twitter_api():
    """测试Twitter API连接和功能"""
    print("🔍 开始诊断Twitter API...")
    print("=" * 50)
    
    # 检查配置
    print("1. 检查配置...")
    try:
        Config.validate()
        print("✅ 配置验证通过")
        print(f"   Bearer Token: {Config.TWITTER_BEARER_TOKEN[:20]}...")
        print(f"   监控用户: @{Config.TWITTER_USERNAME}")
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False
    
    # 测试API连接
    print("\n2. 测试API连接...")
    headers = {
        'Authorization': f'Bearer {Config.TWITTER_BEARER_TOKEN}',
        'User-Agent': 'TeleLuX/1.0'
    }
    
    try:
        # 测试基本连接 - 使用公开端点
        test_url = f"https://api.twitter.com/2/users/by/username/{Config.TWITTER_USERNAME}"
        response = requests.get(
            test_url,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            print("✅ API连接正常")
        else:
            print(f"❌ API连接失败: {response.status_code}")
            print(f"   响应: {response.text}")

            # 如果是403错误，尝试使用v1.1 API
            if response.status_code == 403:
                print("⚠️  尝试使用Twitter API v1.1...")
                v1_url = f"https://api.twitter.com/1.1/users/show.json?screen_name={Config.TWITTER_USERNAME}"
                v1_response = requests.get(v1_url, headers=headers, timeout=10)

                if v1_response.status_code == 200:
                    print("✅ Twitter API v1.1连接正常")
                    return True
                else:
                    print(f"❌ Twitter API v1.1也失败: {v1_response.status_code}")
                    return False
            else:
                return False
            
    except Exception as e:
        print(f"❌ 网络连接失败: {e}")
        return False
    
    # 测试用户查找
    print("\n3. 测试用户查找...")
    try:
        user_url = f"https://api.twitter.com/2/users/by/username/{Config.TWITTER_USERNAME}"
        response = requests.get(user_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            if 'data' in user_data:
                user_id = user_data['data']['id']
                print(f"✅ 用户查找成功")
                print(f"   用户ID: {user_id}")
                print(f"   用户名: @{user_data['data']['username']}")
            else:
                print(f"❌ 用户数据异常: {user_data}")
                return False
        else:
            print(f"❌ 用户查找失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 用户查找异常: {e}")
        return False
    
    # 测试推文获取
    print("\n4. 测试推文获取...")
    try:
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {
            'max_results': 5,
            'tweet.fields': 'created_at,public_metrics',
            'exclude': 'retweets,replies'
        }
        
        response = requests.get(tweets_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            tweets_data = response.json()
            if 'data' in tweets_data and tweets_data['data']:
                tweets = tweets_data['data']
                print(f"✅ 推文获取成功")
                print(f"   获取到 {len(tweets)} 条推文")
                
                # 显示最新推文信息
                latest_tweet = tweets[0]
                print(f"\n📝 最新推文:")
                print(f"   ID: {latest_tweet['id']}")
                print(f"   内容: {latest_tweet['text'][:100]}...")
                print(f"   时间: {latest_tweet['created_at']}")
                
                return True
            else:
                print(f"❌ 推文数据为空: {tweets_data}")
                return False
        else:
            print(f"❌ 推文获取失败: {response.status_code}")
            print(f"   响应: {response.text}")
            
            # 检查是否是速率限制
            if response.status_code == 429:
                print("⚠️  这是Twitter API速率限制错误")
                print("   建议等待15分钟后重试")
                
                # 检查速率限制信息
                if 'x-rate-limit-reset' in response.headers:
                    reset_time = int(response.headers['x-rate-limit-reset'])
                    reset_datetime = datetime.fromtimestamp(reset_time)
                    print(f"   速率限制重置时间: {reset_datetime}")
            
            return False
            
    except Exception as e:
        print(f"❌ 推文获取异常: {e}")
        return False

def check_rate_limits():
    """检查API速率限制状态"""
    print("\n5. 检查速率限制状态...")
    
    headers = {
        'Authorization': f'Bearer {Config.TWITTER_BEARER_TOKEN}',
        'User-Agent': 'TeleLuX/1.0'
    }
    
    try:
        # 获取速率限制信息
        response = requests.get(
            'https://api.twitter.com/1.1/application/rate_limit_status.json',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            rate_data = response.json()
            
            # 检查用户相关的限制
            if 'resources' in rate_data:
                users_limits = rate_data['resources'].get('users', {})
                tweets_limits = rate_data['resources'].get('statuses', {})
                
                print("📊 速率限制状态:")
                
                # 用户查找限制
                if '/users/by/username/:username' in users_limits:
                    user_limit = users_limits['/users/by/username/:username']
                    print(f"   用户查找: {user_limit['remaining']}/{user_limit['limit']}")
                
                # 推文获取限制
                if '/users/:id/tweets' in users_limits:
                    tweets_limit = users_limits['/users/:id/tweets']
                    print(f"   推文获取: {tweets_limit['remaining']}/{tweets_limit['limit']}")
                    
                    if tweets_limit['remaining'] == 0:
                        reset_time = datetime.fromtimestamp(tweets_limit['reset'])
                        print(f"   ⚠️  推文获取已达限制，重置时间: {reset_time}")
                
        else:
            print(f"❌ 无法获取速率限制信息: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 检查速率限制失败: {e}")

def main():
    """主函数"""
    print("🔧 Twitter API 诊断工具")
    print("=" * 50)
    
    try:
        # 基本API测试
        if test_twitter_api():
            print("\n🎉 所有测试通过！Twitter API工作正常")
        else:
            print("\n❌ 检测到问题，请查看上述错误信息")
        
        # 速率限制检查
        check_rate_limits()
        
    except KeyboardInterrupt:
        print("\n⏹️  诊断已取消")
    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 诊断完成")

if __name__ == "__main__":
    main()
