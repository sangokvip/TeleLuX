#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter API详细诊断脚本
"""

import sys
import traceback
import requests
from config import Config

def test_twitter_detailed():
    """详细测试Twitter API连接"""
    print("=== Twitter API详细诊断 ===")
    
    try:
        # 检查配置
        print("1. 检查Twitter配置...")
        bearer_token = Config.TWITTER_BEARER_TOKEN
        if not bearer_token:
            print("错误: Twitter Bearer Token未配置")
            return False
        
        print(f"Bearer Token: {bearer_token[:20]}...")
        
        # 测试基本API连接
        print("\n2. 测试基本API连接...")
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'User-Agent': 'TeleLuX/1.0'
        }
        
        # 测试获取当前用户信息（使用Twitter API v2）
        test_url = "https://api.twitter.com/2/users/me"
        response = requests.get(test_url, headers=headers, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("基本API连接成功")
            data = response.json()
            if 'data' in data:
                print(f"当前用户: @{data['data'].get('username', 'unknown')}")
        elif response.status_code == 401:
            print("认证失败 - Bearer Token可能无效")
            print(f"响应内容: {response.text}")
            return False
        elif response.status_code == 403:
            print("权限不足 - 需要提升API权限")
            print(f"响应内容: {response.text}")
            return False
        elif response.status_code == 429:
            print("速率限制 - 需要等待")
            print(f"响应内容: {response.text}")
            return False
        else:
            print(f"未知错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        # 测试获取指定用户信息
        print(f"\n3. 测试获取指定用户信息...")
        username = Config.TWITTER_USERNAME
        if username:
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            user_response = requests.get(user_url, headers=headers, timeout=10)
            
            print(f"用户查询响应状态码: {user_response.status_code}")
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                if 'data' in user_data:
                    user_info = user_data['data']
                    print(f"找到用户: @{user_info['username']}")
                    print(f"用户ID: {user_info['id']}")
                    print(f"名称: {user_info.get('name', 'N/A')}")
                    
                    # 测试获取用户推文
                    print(f"\n4. 测试获取用户推文...")
                    user_id = user_info['id']
                    tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
                    params = {
                        'max_results': 5,
                        'tweet.fields': 'created_at,public_metrics'
                    }
                    
                    tweets_response = requests.get(tweets_url, headers=headers, params=params, timeout=10)
                    print(f"推文查询响应状态码: {tweets_response.status_code}")
                    
                    if tweets_response.status_code == 200:
                        tweets_data = tweets_response.json()
                        if 'data' in tweets_data:
                            tweets = tweets_data['data']
                            print(f"获取到 {len(tweets)} 条推文")
                            for i, tweet in enumerate(tweets[:2], 1):
                                print(f"  推文{i}: {tweet.get('text', 'N/A')[:50]}...")
                        else:
                            print("未获取到推文数据")
                    else:
                        print(f"获取推文失败: {tweets_response.text}")
                else:
                    print("未找到用户数据")
            elif user_response.status_code == 404:
                print(f"用户 @{username} 不存在")
            else:
                print(f"获取用户信息失败: {user_response.text}")
        else:
            print("未配置Twitter用户名")
        
        return True
        
    except requests.exceptions.Timeout:
        print("请求超时 - 网络连接问题")
        return False
    except requests.exceptions.ConnectionError:
        print("连接错误 - 无法连接到Twitter API")
        return False
    except Exception as e:
        print(f"测试失败: {e}")
        traceback.print_exc()
        return False

def test_tweepy_integration():
    """测试Tweepy集成"""
    print("\n=== 测试Tweepy集成 ===")
    
    try:
        import tweepy
        from config import Config
        
        # 创建Tweepy客户端
        print("正在创建Tweepy客户端...")
        client = tweepy.Client(
            bearer_token=Config.TWITTER_BEARER_TOKEN,
            wait_on_rate_limit=True
        )
        
        # 测试获取当前用户信息
        print("正在测试Tweepy客户端...")
        try:
            me = client.get_me()
            if me.data:
                print(f"Tweepy客户端创建成功 - 当前用户: @{me.data.username}")
            else:
                print("Tweepy客户端创建成功，但无法获取当前用户信息")
        except Exception as e:
            print(f"Tweepy客户端测试失败: {e}")
            return False
        
        # 测试获取指定用户
        username = Config.TWITTER_USERNAME
        if username:
            print(f"正在获取 @{username} 的用户信息...")
            try:
                user = client.get_user(username=username)
                if user.data:
                    print(f"获取用户成功: @{user.data.username} (ID: {user.data.id})")
                    
                    # 测试获取推文
                    print(f"正在获取 @{username} 的推文...")
                    tweets = client.get_users_tweets(
                        id=user.data.id,
                        max_results=5,
                        tweet_fields=['created_at', 'public_metrics']
                    )
                    
                    if tweets.data:
                        print(f"获取推文成功: {len(tweets.data)} 条")
                        for i, tweet in enumerate(tweets.data[:2], 1):
                            print(f"  推文{i}: {tweet.text[:50]}...")
                    else:
                        print("未获取到推文")
                else:
                    print("未找到用户")
            except Exception as e:
                print(f"Tweepy获取用户失败: {e}")
                return False
        else:
            print("未配置Twitter用户名")
        
        return True
        
    except ImportError:
        print("Tweepy未安装")
        return False
    except Exception as e:
        print(f"Tweepy测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("Twitter API详细诊断测试")
    print("=" * 60)
    
    # 测试原始HTTP请求
    http_result = test_twitter_detailed()
    
    # 测试Tweepy集成
    tweepy_result = test_tweepy_integration()
    
    print("\n" + "=" * 60)
    print("诊断结果:")
    print(f"HTTP API测试: {'通过' if http_result else '失败'}")
    print(f"Tweepy测试: {'通过' if tweepy_result else '失败'}")
    
    if http_result and tweepy_result:
        print("Twitter API功能正常")
        return 0
    else:
        print("Twitter API存在问题，请检查上述错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())