#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter推文图片问题诊断脚本
"""

import sys
import requests
from config import Config

def test_tweet_with_media():
    """测试包含图片的推文"""
    print("=== Twitter推文图片问题诊断 ===")
    
    try:
        # 使用Bearer Token
        headers = {
            'Authorization': f'Bearer {Config.TWITTER_BEARER_TOKEN}',
            'User-Agent': 'TeleLuX/1.0'
        }
        
        # 测试一个已知包含图片的推文
        test_tweet_id = "1234567890"  # 你可以替换为实际的推文ID
        
        print(f"1. 测试推文详情获取...")
        
        # 获取推文详情，包含媒体信息
        tweet_url = f"https://api.twitter.com/2/tweets/{test_tweet_id}"
        params = {
            'tweet.fields': 'created_at,public_metrics,attachments',
            'expansions': 'attachments.media_keys,author_id',
            'media.fields': 'url,type,preview_image_url',
            'user.fields': 'username,name'
        }
        
        response = requests.get(tweet_url, headers=headers, params=params, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("推文数据:", data)
            
            # 检查是否包含媒体
            if 'includes' in data and 'media' in data['includes']:
                print("找到媒体信息:")
                for media in data['includes']['media']:
                    print(f"媒体类型: {media.get('type', 'unknown')}")
                    print(f"媒体URL: {media.get('url', media.get('preview_image_url', '无URL'))}")
            else:
                print("未找到媒体信息")
                
            # 检查推文附件
            if 'data' in data and 'attachments' in data['data']:
                print("推文附件:", data['data']['attachments'])
            else:
                print("推文无附件")
                
        else:
            print(f"获取推文失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def explain_twitter_media_issue():
    """解释Twitter媒体问题"""
    print("\n=== Twitter推文图片问题解释 ===")
    
    print("""
常见问题原因：

1. **API权限限制**
   - 免费Twitter API可能无法获取完整的媒体信息
   - 需要Elevated权限才能访问媒体URL

2. **媒体类型限制**
   - 视频推文可能只返回预览图，不是原图
   - 多张图片的推文可能只显示第一张

3. **URL访问限制**
   - Twitter图片URL可能需要特殊认证
   - 某些图片可能需要登录才能查看

4. **API版本差异**
   - v2 API对媒体信息的返回有限制
   - 可能需要使用v1.1 API获取完整媒体信息

5. **推文隐私设置**
   - 私密账号的推文图片无法通过API获取
   - 受保护的内容不会返回媒体URL

解决方案：

1. **检查API权限级别**
   - 确保有Elevated或更高权限
   - 在项目设置中启用媒体访问权限

2. **使用正确的API端点**
   - 包含expansions=attachments.media_keys参数
   - 请求media.fields=url,preview_image_url

3. **处理不同类型的媒体**
   - 图片：使用url字段
   - 视频：使用preview_image_url字段
   - GIF：特殊处理

4. **备用方案**
   - 如果没有媒体URL，显示推文文本
   - 提供原推文链接让用户点击查看

5. **权限验证**
   - 检查Bearer Token的有效性
   - 确认项目有访问媒体资源的权限
""")

def main():
    """主函数"""
    print("Twitter推文图片问题诊断")
    print("=" * 60)
    
    # 解释问题
    explain_twitter_media_issue()
    
    # 运行测试（如果有配置的话）
    print("\n运行实际测试...")
    try:
        from config import Config
        Config._init_configs()
        
        if Config.TWITTER_BEARER_TOKEN:
            test_tweet_with_media()
        else:
            print("未配置Twitter Bearer Token，跳过实际测试")
            
    except Exception as e:
        print(f"测试过程出错: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())