import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置管理类"""
    
    # Twitter API 配置
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    # Telegram Bot 配置
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')  # bryansuperb 的 Chat ID
    
    # 监控配置
    TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')  # 要监控的Twitter用户名
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))  # 检查间隔（秒），默认5分钟
    
    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'tweets.db')

    @classmethod
    def require_telegram(cls, require_chat_id=False, require_admin=False):
        missing = []

        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')

        if require_chat_id and not cls.TELEGRAM_CHAT_ID:
            missing.append('TELEGRAM_CHAT_ID')

        if require_admin and not cls.ADMIN_CHAT_ID:
            missing.append('ADMIN_CHAT_ID')

        if missing:
            raise ValueError(f"缺少必要的Telegram配置: {', '.join(missing)}")

        return True

    @classmethod
    def validate(cls):
        """验证必要的配置是否存在"""
        required_configs = [
            'TWITTER_BEARER_TOKEN',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHAT_ID',
            'TWITTER_USERNAME'
        ]
        
        missing_configs = []
        for config in required_configs:
            if not getattr(cls, config):
                missing_configs.append(config)
        
        if missing_configs:
            raise ValueError(f"缺少必要的配置: {', '.join(missing_configs)}")
        
        return True
