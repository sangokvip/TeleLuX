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
                
                # 创建黑名单表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blacklist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE NOT NULL,
                        user_name TEXT,
                        username TEXT,
                        reason TEXT DEFAULT '多次离群',
                        leave_count INTEGER DEFAULT 0,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        added_by TEXT DEFAULT 'system'
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
    def add_to_blacklist(self, user_id, user_name, username, leave_count, reason="多次离群"):
        """将用户添加到黑名单"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO blacklist 
                    (user_id, user_name, username, reason, leave_count, added_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, user_name, username, reason, leave_count))
                conn.commit()
                logger.info(f"用户 {user_name} (ID: {user_id}) 已添加到黑名单")
                return True
        except Exception as e:
            logger.error(f"添加用户到黑名单失败: {e}")
            return False
    
    def is_user_blacklisted(self, user_id):
        """检查用户是否在黑名单中"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM blacklist WHERE user_id = ?', (user_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"检查黑名单状态失败: {e}")
            return False
    
    def get_blacklist(self):
        """获取黑名单列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, user_name, username, reason, leave_count, added_at 
                    FROM blacklist 
                    ORDER BY added_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取黑名单失败: {e}")
            return []
    
    def remove_from_blacklist(self, user_id):
        """从黑名单中移除用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM blacklist WHERE user_id = ?', (user_id,))
                removed = cursor.rowcount > 0
                conn.commit()
                if removed:
                    logger.info(f"用户 ID {user_id} 已从黑名单中移除")
                return removed
        except Exception as e:
            logger.error(f"从黑名单移除用户失败: {e}")
            return False
    
    def get_blacklist_count(self):
        """获取黑名单用户数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM blacklist')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"获取黑名单数量失败: {e}")
            return 0