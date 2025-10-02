import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置管理类"""
    
    @classmethod
    def get_config(cls, key: str, default: str = None, required: bool = False) -> str:
        """
        获取配置值
        
        Args:
            key: 配置键名
            default: 默认值
            required: 是否必需
            
        Returns:
            配置值
            
        Raises:
            ValueError: 如果required为True且配置不存在
        """
        value = os.getenv(key, default)
        if required and not value:
            raise ValueError(f"缺少必需的环境变量: {key}")
        return value
    
    @classmethod
    def get_int_config(cls, key: str, default: int = 0, required: bool = False) -> int:
        """
        获取整数类型的配置值
        
        Args:
            key: 配置键名
            default: 默认值
            required: 是否必需
            
        Returns:
            整数配置值
            
        Raises:
            ValueError: 如果required为True且配置不存在，或者值不能转换为整数
        """
        value = cls.get_config(key, None, required=False)
        if value is None:
            return default
        
        try:
            return int(value)
        except (ValueError, TypeError):
            if required:
                raise ValueError(f"配置 {key} 的值 '{value}' 不能转换为整数")
            return default
    
    @classmethod
    def get_bool_config(cls, key: str, default: bool = False) -> bool:
        """
        获取布尔类型的配置值
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            布尔配置值
        """
        value = cls.get_config(key, str(default).lower())
        if value is None:
            return default
        
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    # Twitter API 配置
    TWITTER_BEARER_TOKEN = None
    TWITTER_API_KEY = None
    TWITTER_API_SECRET = None
    TWITTER_ACCESS_TOKEN = None
    TWITTER_ACCESS_TOKEN_SECRET = None
    
    # Telegram Bot 配置
    TELEGRAM_BOT_TOKEN = None
    TELEGRAM_CHAT_ID = None
    ADMIN_CHAT_ID = None  # bryansuperb 的 Chat ID
    
    # 监控配置
    TWITTER_USERNAME = None  # 要监控的Twitter用户名
    CHECK_INTERVAL = 300  # 检查间隔（秒），默认5分钟
    
    # 数据库配置
    DATABASE_PATH = 'tweets.db'
    
    @classmethod
    def _init_configs(cls):
        """初始化配置（在类加载后调用）"""
        # Twitter API 配置
        cls.TWITTER_BEARER_TOKEN = cls.get_config('TWITTER_BEARER_TOKEN', required=True)
        cls.TWITTER_API_KEY = cls.get_config('TWITTER_API_KEY')
        cls.TWITTER_API_SECRET = cls.get_config('TWITTER_API_SECRET')
        cls.TWITTER_ACCESS_TOKEN = cls.get_config('TWITTER_ACCESS_TOKEN')
        cls.TWITTER_ACCESS_TOKEN_SECRET = cls.get_config('TWITTER_ACCESS_TOKEN_SECRET')
        
        # Telegram Bot 配置
        cls.TELEGRAM_BOT_TOKEN = cls.get_config('TELEGRAM_BOT_TOKEN', required=True)
        cls.TELEGRAM_CHAT_ID = cls.get_config('TELEGRAM_CHAT_ID', required=True)
        cls.ADMIN_CHAT_ID = cls.get_config('ADMIN_CHAT_ID')  # bryansuperb 的 Chat ID
        
        # 监控配置
        cls.TWITTER_USERNAME = cls.get_config('TWITTER_USERNAME', required=True)  # 要监控的Twitter用户名
        cls.CHECK_INTERVAL = cls.get_int_config('CHECK_INTERVAL', 300)  # 检查间隔（秒），默认5分钟
        
        # 数据库配置
        cls.DATABASE_PATH = cls.get_config('DATABASE_PATH', 'tweets.db')
    
    @classmethod
    def validate(cls):
        """验证必要的配置是否存在"""
        # 首先初始化配置
        cls._init_configs()
        
        required_configs = [
            'TWITTER_BEARER_TOKEN',
            'TELEGRAM_BOT_TOKEN', 
            'TELEGRAM_CHAT_ID',
            'TWITTER_USERNAME'
        ]
        
        missing_configs = []
        for config in required_configs:
            try:
                # 重新获取以触发验证
                cls.get_config(config, required=True)
            except ValueError as e:
                missing_configs.append(config)
        
        if missing_configs:
            raise ValueError(f"缺少必要的配置: {', '.join(missing_configs)} (请检查环境变量)")
        
        return True
