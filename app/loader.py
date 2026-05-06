import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession

from app.config import config
from app.models.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot: Bot | None = None
dp: Dispatcher | None = None


async def load():
    global bot, dp

    session = AiohttpSession()
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session
    )
    dp = Dispatcher(storage=MemoryStorage())

    await init_db()
    logger.info("Database initialized")

    _load_handlers()
    logger.info("Handlers loaded")


def _load_handlers():
    from app.handlers import commands, manga, callbacks
    dp.include_router(commands.router)
    dp.include_router(manga.router)
    dp.include_router(callbacks.router)


async def start():
    await load()
    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started!")
    await dp.start_polling(bot)


async def close():
    await bot.session.close()
    logger.info("Bot closed")
