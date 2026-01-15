import tweepy
import logging
from datetime import datetime, timezone, timedelta
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

            logger.info(f"开始获取用户 {username} (ID: {user_id}) 的推文...")

            # 方法1: 尝试获取所有类型的推文
            try:
                tweets = self.client.get_users_tweets(
                    id=user_id,
                    max_results=count,
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets'],
                    # 不排除任何内容，先看看有什么
                )

                if tweets.data:
                    logger.info(f"方法1成功: 获取到 {len(tweets.data)} 条推文")

                    # 分析推文类型
                    original_tweets = []
                    retweets = []
                    replies = []

                    for tweet in tweets.data:
                        if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                            ref_type = tweet.referenced_tweets[0].type
                            if ref_type == 'retweeted':
                                retweets.append(tweet)
                            elif ref_type == 'replied_to':
                                replies.append(tweet)
                        else:
                            original_tweets.append(tweet)

                    logger.info(f"推文分析: 原创{len(original_tweets)}条, 转推{len(retweets)}条, 回复{len(replies)}条")

                    # 优先返回原创推文，如果没有则返回所有推文
                    tweets_to_process = original_tweets if original_tweets else tweets.data

                else:
                    logger.warning("方法1: 没有获取到任何推文数据")
                    tweets_to_process = []

            except Exception as e:
                logger.error(f"方法1失败: {e}")
                tweets_to_process = []

            # 方法2: 如果方法1失败，尝试只获取原创推文
            if not tweets_to_process:
                try:
                    logger.info("尝试方法2: 只获取原创推文...")
                    tweets = self.client.get_users_tweets(
                        id=user_id,
                        max_results=count,
                        tweet_fields=['created_at', 'public_metrics'],
                        exclude=['retweets', 'replies']
                    )

                    if tweets.data:
                        logger.info(f"方法2成功: 获取到 {len(tweets.data)} 条原创推文")
                        tweets_to_process = tweets.data
                    else:
                        logger.warning("方法2: 没有获取到原创推文")

                except Exception as e:
                    logger.error(f"方法2失败: {e}")

            # 处理获取到的推文
            if not tweets_to_process:
                logger.warning(f"用户 {username} 暂无可获取的推文")
                return []

            tweet_list = []
            for tweet in tweets_to_process:
                tweet_info = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'url': f"https://twitter.com/{username}/status/{tweet.id}",
                    'username': username
                }
                tweet_list.append(tweet_info)

            logger.info(f"最终处理了 {len(tweet_list)} 条推文")
            return tweet_list

        except Exception as e:
            logger.error(f"获取推文失败: {e}")
            return []

    def get_recent_tweets(self, username, count=3, days=7):
        """获取用户在指定天数内的最新推文"""
        try:
            user_id = self.get_user_id(username)
            if not user_id:
                return []

            # 计算时间范围
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days)

            logger.info(f"获取用户 {username} 在 {start_time.strftime('%Y-%m-%d')} 到 {end_time.strftime('%Y-%m-%d')} 期间的推文...")

            try:
                # 使用时间范围获取推文
                tweets = self.client.get_users_tweets(
                    id=user_id,
                    max_results=min(count * 3, 100),  # 获取更多推文以便过滤
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets'],
                    start_time=start_time,
                    end_time=end_time,
                    exclude=['retweets', 'replies']  # 只要原创推文
                )

                if tweets.data:
                    logger.info(f"在指定时间范围内获取到 {len(tweets.data)} 条推文")

                    # 按时间排序（最新的在前）
                    sorted_tweets = sorted(tweets.data, key=lambda x: x.created_at, reverse=True)

                    # 取前N条
                    recent_tweets = sorted_tweets[:count]

                    tweet_list = []
                    for tweet in recent_tweets:
                        # 确保推文在时间范围内
                        if start_time <= tweet.created_at <= end_time:
                            tweet_info = {
                                'id': tweet.id,
                                'text': tweet.text,
                                'created_at': tweet.created_at,
                                'url': f"https://twitter.com/{username}/status/{tweet.id}",
                                'username': username
                            }
                            tweet_list.append(tweet_info)

                    logger.info(f"过滤后获得 {len(tweet_list)} 条符合条件的推文")
                    return tweet_list

                else:
                    logger.info(f"用户 {username} 在过去{days}天内没有发布推文")
                    return []

            except Exception as e:
                logger.error(f"使用时间范围获取推文失败: {e}")

                # 如果时间范围查询失败，回退到普通查询然后过滤
                logger.info("回退到普通查询方式...")
                all_tweets = self.get_latest_tweets(username, count * 2)

                if all_tweets:
                    # 手动过滤时间范围
                    recent_tweets = []
                    for tweet in all_tweets:
                        tweet_time = tweet['created_at']
                        if isinstance(tweet_time, str):
                            tweet_time = datetime.fromisoformat(tweet_time.replace('Z', '+00:00'))

                        if start_time <= tweet_time <= end_time:
                            recent_tweets.append(tweet)

                    # 按时间排序并取前N条
                    recent_tweets.sort(key=lambda x: x['created_at'], reverse=True)
                    result = recent_tweets[:count]

                    logger.info(f"回退方式获得 {len(result)} 条符合条件的推文")
                    return result
                else:
                    return []

        except Exception as e:
            logger.error(f"获取指定时间范围推文失败: {e}")
            return []

    def get_tweet_by_id(self, tweet_id):
        """根据推文ID获取推文详情"""
        try:
            logger.info(f"获取推文详情: {tweet_id}")

            # 获取推文信息
            tweet = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                user_fields=['username', 'name'],
                expansions=['author_id']
            )

            if not tweet.data:
                logger.error(f"推文不存在: {tweet_id}")
                return None

            # 获取作者信息
            author_username = "unknown"
            if tweet.includes and 'users' in tweet.includes:
                for user in tweet.includes['users']:
                    if user.id == tweet.data.author_id:
                        author_username = user.username
                        break

            tweet_info = {
                'id': tweet.data.id,
                'text': tweet.data.text,
                'created_at': tweet.data.created_at,
                'url': f"https://twitter.com/{author_username}/status/{tweet.data.id}",
                'username': author_username,
                'author_id': tweet.data.author_id
            }

            logger.info(f"成功获取推文: @{author_username} - {tweet.data.text[:50]}...")
            return tweet_info

        except tweepy.NotFound:
            logger.error(f"推文不存在或已被删除: {tweet_id}")
            return None
        except tweepy.Unauthorized:
            logger.error(f"无权访问推文: {tweet_id}")
            return None
        except Exception as e:
            logger.error(f"获取推文详情失败: {e}")
            return None
    
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
