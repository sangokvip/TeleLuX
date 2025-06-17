import sqlite3
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class Database:
    """数据库操作类"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processed_tweets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tweet_id TEXT UNIQUE NOT NULL,
                        username TEXT NOT NULL,
                        tweet_url TEXT NOT NULL,
                        tweet_text TEXT,
                        created_at TIMESTAMP NOT NULL,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def is_tweet_processed(self, tweet_id):
        """检查推文是否已经处理过"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM processed_tweets WHERE tweet_id = ?', (tweet_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"检查推文状态失败: {e}")
            return False
    
    def mark_tweet_processed(self, tweet_id, username, tweet_url, tweet_text, created_at):
        """标记推文为已处理"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO processed_tweets 
                    (tweet_id, username, tweet_url, tweet_text, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tweet_id, username, tweet_url, tweet_text, created_at))
                conn.commit()
                logger.info(f"推文 {tweet_id} 标记为已处理")
                return True
        except Exception as e:
            logger.error(f"标记推文失败: {e}")
            return False
    
    def get_processed_tweets_count(self):
        """获取已处理的推文数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM processed_tweets')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"获取推文数量失败: {e}")
            return 0
    
    def cleanup_old_records(self, days=30):
        """清理旧记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM processed_tweets 
                    WHERE processed_at < datetime('now', '-{} days')
                '''.format(days))
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"清理了 {deleted_count} 条旧记录")
                return deleted_count
        except Exception as e:
            logger.error(f"清理旧记录失败: {e}")
            return 0
