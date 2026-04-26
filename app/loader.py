import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp

from app.config import config
from app.models.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Loader:
    bot: Bot
    dp: Dispatcher
    storage: MemoryStorage
    
    @classmethod
    async def load(cls):
        # Используем Cloudflare DNS для обхода блокировок
        from aiogram.client.session.aiohttp import AiohttpSession
        
        session = AiohttpSession()
        
        cls.bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            session=session
        )
        cls.storage = MemoryStorage()
        cls.dp = Dispatcher(storage=cls.storage)
        
        await init_db()
        logger.info("Database initialized")
        
        await cls._load_handlers()
        logger.info("Handlers loaded")
        logger.info("Using system DNS through Hiddify TUN for all connections")
    
    @classmethod
    async def _load_handlers(cls):
        from app.handlers import commands, manga, callbacks
        
        router = cls.dp.include_router
        
        router(commands.router)
        router(manga.router)
        router(callbacks.router)
    
    @classmethod
    async def start(cls):
        await cls.load()
        logger.info("Telegram via TUN, MangaLib direct - starting bot...")
        await cls.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot started successfully!")
        await cls.dp.start_polling(cls.bot)
    
    @classmethod
    async def close(cls):
        await cls.bot.session.close()
        logger.info("Bot closed")


async def main():
    loader = Loader()
    await loader.start()


if __name__ == "__main__":
    asyncio.run(main())
