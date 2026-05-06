import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    PROXY_URL: str = os.getenv("PROXY_URL", "")

    MAX_FILE_SIZE_TG: int = 50 * 1024 * 1024
    COMPRESSION_QUALITY: int = 85
    MAX_IMAGE_DIMENSION: int = 2000


config = Config()
