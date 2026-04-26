import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "bot_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "bot_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "telegram_bot")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    
    PROXY_URL: str = os.getenv("PROXY_URL", "")
    
    MAX_FILE_SIZE_TG: int = 50 * 1024 * 1024
    COMPRESSION_QUALITY: int = 85
    MAX_IMAGE_DIMENSION: int = 2000
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "true").lower() == "true"


config = Config()
