import aiohttp
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from config import Config
from database import Database

logger = logging.getLogger(__name__)

class TwitterMonitor:
    """Twitter监控类 (基于 RapidAPI twitter241)"""
    
    def __init__(self):
        self.config = Config()
        self.database = Database()
        self.headers = None
        self.base_url = "https://twitter241.p.rapidapi.com"
        self._setup_twitter_api()
    
    def _setup_twitter_api(self):
        """设置 RapidAPI 访问头"""
        try:
            if not Config.RAPIDAPI_KEY:
                logger.warning("未配置 RAPIDAPI_KEY，但模块已初始化")
                
            self.headers = {
                "x-rapidapi-key": Config.RAPIDAPI_KEY,
                "x-rapidapi-host": "twitter241.p.rapidapi.com"
            }
            logger.info("RapidAPI (Twtttr) 初始化成功")

        except Exception as e:
            logger.error(f"API初始化失败: {e}")
            raise

    async def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """封装 aiohttp 请求"""
        url = f"https://twitter241.p.rapidapi.com{endpoint}"
        
        # 因为在常规循环里调用可能是同步结构，虽然是 async 方法
        # 实际调用的主类如果不在协程里，需要用 asyncio.run，
        # 但既然原本 TeleLuxBot 运行在 asyncio loop 中，我们会确保这正常工作。
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 429:
                        logger.warning(f"RapidAPI 触发速率限制")
                        return None
                    if response.status != 200:
                        logger.error(f"API请求失败: {response.status} - {await response.text()}")
                        return None
                    return await response.json()
        except Exception as e:
            logger.error(f"网络请求错误: {e}")
            return None

    def _is_rate_limit_error(self, e: Exception) -> bool:
        return '429' in str(e) or 'too many requests' in str(e).lower()
    
    async def get_user_id(self, username):
        """根据用户名获取用户ID (基于 twitter241 API /user)"""
        try:
            username = username.lstrip('@')
            
            data = await self._make_request("/user", {"username": username})
            if data and data.get("result", {}).get("data", {}).get("user", {}):
                rest_id = data["result"]["data"]["user"]["result"]["rest_id"]
                logger.info(f"获取用户ID成功: {username} -> {rest_id}")
                return rest_id
            else:
                logger.error(f"用户不存在或结构变更: {username}")
                return None
                
        except Exception as e:
            logger.error(f"获取用户ID失败: {e}")
            return None

    def _extract_media_info_from_legacy(self, legacy_tweet: dict) -> dict:
        """从解析到的 legacy json 中提取媒体 (Twtttr 接口格式)"""
        media_items = []
        media_urls = []
        preview_image_url = None

        extended_entities = legacy_tweet.get("extended_entities", {})
        media_list = extended_entities.get("media", [])
        
        for m in media_list:
            media_type = m.get("type")
            media_url = m.get("media_url_https")
            
            if media_type == "video" or media_type == "animated_gif":
                # 寻找视频链接中最高分辨率的
                variants = m.get("video_info", {}).get("variants", [])
                best_video_url = None
                max_bitrate = -1
                for v in variants:
                    if v.get("content_type") == "video/mp4" and v.get("bitrate", -1) > max_bitrate:
                        max_bitrate = v.get("bitrate")
                        best_video_url = v.get("url")
                
                if best_video_url:
                    media_url = best_video_url
                
            media_items.append({
                'type': media_type,
                'url': media_url,
                'preview_image_url': m.get("media_url_https")
            })
            if media_url:
                media_urls.append(media_url)
            if not preview_image_url:
                preview_image_url = m.get("media_url_https")

        return {
            'has_media': len(media_items) > 0,
            'media_urls': media_urls,
            'preview_image_url': preview_image_url,
            'media': media_items
        }
    
    async def get_latest_tweets(self, username, count=10):
        """获取用户最新的推文 (基于 twitter241 API /user-tweets)"""
        try:
            user_id = await self.get_user_id(username)
            if not user_id:
                return []

            logger.info(f"开始获取用户 {username} (ID: {user_id}) 的推文...")
            
            # 为 twitter241 的 /user-tweets 准备参数（测试发现参数叫 user 而非 user_id）
            params = {
                "user": user_id,
                "count": count
            }
            
            data = await self._make_request("/user-tweets", params)
            if not data:
                return []

            # 解析推文 (twitter241 的 /user-tweets 结构为 result.timeline.instructions)
            instructions = data.get("result", {}).get("timeline", {}).get("instructions", [])
            
            tweet_list = []
            
            try:
                entries = []
                for inst in instructions:
                    if inst.get("type") == "TimelineAddEntries":
                        entries = inst.get("entries", [])
                        break
                
                logger.info(f"提取到 {len(entries)} 条内容项")
                
                for entry in entries:
                    content = entry.get("content", {})
                    # 我们只处理普通的 Tweet
                    if content.get("entryType") == "TimelineTimelineItem":
                        item_result = content.get("itemContent", {}).get("tweet_results", {}).get("result", {})
                        
                        # 排除转推 (可以看情况保留，这里暂时过滤被转推内容的嵌套结构)
                        legacy = item_result.get("legacy", {})
                        if not legacy or legacy.get("retweeted_status_result"):
                            continue  # 跳过转推
                        
                        tweet_id = legacy.get("id_str")
                        text = legacy.get("full_text")
                        
                        # 将时间字符串 "Sat Oct 14 00:00:00 +0000 2023" 转为 datetime 对象
                        # 或者为了兼容下游直接存 string，如果外层是 datetime 建议使用 parsed
                        created_at_str = legacy.get("created_at")
                        try:
                            # 格式化日期：Sat Dec 14 02:45:00 +0000 2019
                            dt = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S %z %Y')
                        except:
                            dt = created_at_str  # fallback

                        media_info = self._extract_media_info_from_legacy(legacy)

                        tweet_info = {
                            'id': int(tweet_id) if tweet_id else 0,
                            'text': text,
                            'created_at': dt,
                            'url': f"https://twitter.com/{username}/status/{tweet_id}",
                            'username': username,
                            **media_info
                        }
                        tweet_list.append(tweet_info)
                        
                        if len(tweet_list) >= count:
                            break
                            
            except KeyError as e:
                logger.error(f"解析 JSON 结构出错，请检查 RapidAPI 结构是否更改: {e}")
                
            logger.info(f"最终捕获了 {len(tweet_list)} 条有效推文")
            return tweet_list

        except Exception as e:
            logger.error(f"获取推文失败: {e}")
            return []

    async def get_recent_tweets(self, username, count=3, days=7):
        """获取近期推文的大型封装"""
        # 利用 get_latest_tweets 也是获取最新，过滤掉超时的即可
        latest_tweets = await self.get_latest_tweets(username, count=count*2)
        if not latest_tweets:
            return []
            
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        recent_tweets = []
        for tweet in latest_tweets:
            tweet_time = tweet['created_at']
            if isinstance(tweet_time, str):
                try:
                    tweet_time = datetime.strptime(tweet_time, '%a %b %d %H:%M:%S %z %Y')
                except:
                    pass
                    
            if isinstance(tweet_time, datetime):
                # 确保是 timezone 对应的
                if tweet_time.tzinfo is None:
                    tweet_time = tweet_time.replace(tzinfo=timezone.utc)
                if start_time <= tweet_time <= end_time:
                    recent_tweets.append(tweet)
            else:
                # 无法解析时间的默认加进去
                recent_tweets.append(tweet)
                
        return recent_tweets[:count]

    async def get_tweet_by_id(self, tweet_id, username=None):
        """根据推文ID获取推文详情 (使用免费的高可用 api.vxtwitter.com 解决直接获取单推文难题)"""
        try:
            logger.info(f"尝试通过 VxTwitter 接口获取推文详情: {tweet_id}")
            url = f"https://api.vxtwitter.com/Twitter/status/{tweet_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.error(f"VxTwitter 未找到推文 {tweet_id}：{resp.status}")
                        return None
                        
                    data = await resp.json()
                    
                    # 提取媒体
                    media_list = []
                    media_extended = data.get('media_extended', [])
                    for m in media_extended:
                        media_list.append({
                            'url': m.get('url'),
                            'type': m.get('type')  # 'video' or 'image'
                        })
                    
                    # 提取时间
                    created_at_epoch = data.get('date_epoch')
                    if created_at_epoch:
                        dt = datetime.fromtimestamp(created_at_epoch, tz=timezone.utc)
                    else:
                        dt = datetime.now(timezone.utc)
                        
                    # 组合与 get_latest_tweets 结构一致的字典
                    tweet_info = {
                        'id': int(data.get('tweetID', tweet_id)),
                        'text': data.get('text', ''),
                        'created_at': dt,
                        'url': data.get('tweetURL', f"https://twitter.com/i/status/{tweet_id}"),
                        'username': data.get('user_screen_name', username or 'Unknown'),
                        'media': media_list
                    }
                    
                    logger.info(f"成功获取单推文 {tweet_id} 详情！")
                    return tweet_info

        except Exception as e:
            logger.error(f"获取推文 {tweet_id} 详情失败: {e}")
            return None
    
    async def check_new_tweets(self, username):
        """检查新推文"""
        try:
            logger.info(f"开始检查用户 {username} 的新推文")
            
            # 获取最新推文
            latest_tweets = await self.get_latest_tweets(username, count=8)
            
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
                        str(tweet['created_at'])
                    )
            
            if new_tweets:
                logger.info(f"发现 {len(new_tweets)} 条新推文")
            else:
                logger.info("没有发现新推文")
            
            return new_tweets
            
        except Exception as e:
            logger.error(f"检查新推文失败: {e}")
            return []
    
    async def test_connection(self):
        """测试 RapidAPI 连接 (twitter241)"""
        try:
            data = await self._make_request("/user", {"username": "elonmusk"})
            if data and data.get("result"):
                logger.info("RapidAPI (twitter241) 连接测试成功")
                return True
            else:
                logger.error("RapidAPI 连接失败: 无数据返回")
                return False

        except Exception as e:
            logger.error(f"RapidAPI 连接测试失败: {e}")
            return False
