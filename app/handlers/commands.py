import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.keyboards.inline import get_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router()


class UserStates(StatesGroup):
    waiting_for_manga_query = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я бот для поиска и скачивания манги.\n\n"
        "Выберите режим из меню ниже:",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Инструкция по использованию:</b>\n\n"
        "1. <b>Поиск манги</b> - найдите мангу на MangaLib и скачайте главы\n"
        "2. <b>Статистика</b> - посмотрите сколько глав вы скачали\n\n"
        "⏱️ Файлы манги конвертируются в PDF, большие файлы сжимаются."
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    from sqlalchemy import select
    from app.models.database import User, UserStats, get_db
    
    tg_id = message.from_user.id
    
    async for db in get_db():
        result = await db.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("Вы еще ничего не скачивали. Начните поиск!")
            return
        
        stats = user.stats
        if not stats:
            stats = UserStats(user_id=tg_id, manga_chapters_count=0)
        
        await message.answer(
            f"📊 <b>Ваша статистика:</b>\n\n"
            f"📚 <b>Манга:</b> {stats.manga_chapters_count} глав"
        )
        break
