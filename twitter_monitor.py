import tweepy
import logging
from datetime import datetime, timezone
from config import Config
from database import Database

logger = logging.getLogger(__name__)

class TwitterMonitor:
    """Twitter监控类"""
    
    def __init__(self):
        self.config = Config()
        self.database = Database()
        self.api = None
        self.client = None
        self._setup_twitter_api()
    
    def _setup_twitter_api(self):
        """设置Twitter API"""
        try:
            # 使用Bearer Token的客户端（推荐用于读取操作）
            self.client = tweepy.Client(
                bearer_token=Config.TWITTER_BEARER_TOKEN,
                wait_on_rate_limit=True
            )

            # 如果有完整的API密钥，也可以设置API v1.1客户端
            if all([Config.TWITTER_API_KEY, Config.TWITTER_API_SECRET,
                   Config.TWITTER_ACCESS_TOKEN, Config.TWITTER_ACCESS_TOKEN_SECRET]) and \
               Config.TWITTER_API_KEY != 'your_twitter_api_key_here':
                auth = tweepy.OAuthHandler(Config.TWITTER_API_KEY, Config.TWITTER_API_SECRET)
                auth.set_access_token(Config.TWITTER_ACCESS_TOKEN, Config.TWITTER_ACCESS_TOKEN_SECRET)
                self.api = tweepy.API(auth, wait_on_rate_limit=True)

            logger.info("Twitter API初始化成功")

        except Exception as e:
            logger.error(f"Twitter API初始化失败: {e}")
            raise
    
    def get_user_id(self, username):
        """根据用户名获取用户ID"""
        try:
            # 移除@符号（如果存在）
            username = username.lstrip('@')
            
            user = self.client.get_user(username=username)
            if user.data:
                logger.info(f"获取用户ID成功: {username} -> {user.data.id}")
                return user.data.id
            else:
                logger.error(f"用户不存在: {username}")
                return None
                
        except Exception as e:
            logger.error(f"获取用户ID失败: {e}")
            return None
    
    def get_latest_tweets(self, username, count=10):
        """获取用户最新的推文"""
        try:
            user_id = self.get_user_id(username)
            if not user_id:
                return []
            
            # 获取用户推文
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=count,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                exclude=['retweets', 'replies']  # 排除转推和回复
            )
            
            if not tweets.data:
                logger.info(f"用户 {username} 暂无推文")
                return []
            
            tweet_list = []
            for tweet in tweets.data:
                tweet_info = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'url': f"https://twitter.com/{username}/status/{tweet.id}",
                    'username': username
                }
                tweet_list.append(tweet_info)
            
            logger.info(f"获取到 {len(tweet_list)} 条推文")
            return tweet_list
            
        except Exception as e:
            logger.error(f"获取推文失败: {e}")
            return []
    
    def check_new_tweets(self, username):
        """检查新推文"""
        try:
            logger.info(f"开始检查用户 {username} 的新推文")
            
            # 获取最新推文
            latest_tweets = self.get_latest_tweets(username, count=5)
            
            new_tweets = []
            for tweet in latest_tweets:
                # 检查是否已经处理过
                if not self.database.is_tweet_processed(str(tweet['id'])):
                    new_tweets.append(tweet)
                    
                    # 标记为已处理
                    self.database.mark_tweet_processed(
                        str(tweet['id']),
                        tweet['username'],
                        tweet['url'],
                        tweet['text'],
                        tweet['created_at']
                    )
            
            if new_tweets:
                logger.info(f"发现 {len(new_tweets)} 条新推文")
            else:
                logger.info("没有发现新推文")
            
            return new_tweets
            
        except Exception as e:
            logger.error(f"检查新推文失败: {e}")
            return []
    
    def test_connection(self):
        """测试Twitter API连接"""
        try:
            # 使用Bearer Token只能访问公开数据，测试获取一个公开用户
            test_user = self.client.get_user(username="twitter")
            if test_user.data:
                logger.info(f"Twitter API连接成功")
                return True
            else:
                logger.error("Twitter API连接失败")
                return False

        except Exception as e:
            logger.error(f"Twitter API连接测试失败: {e}")
            return False
