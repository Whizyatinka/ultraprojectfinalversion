import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bs4 import BeautifulSoup

from app.handlers.commands import UserStates
from app.models.database import get_db
from app.keyboards.inline import get_manga_card_keyboard, get_search_keyboard
from app.services.manga_service import MangaService

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == "🔍 Поиск манги")
async def manga_search_start(message: Message, state: FSMContext):
    logger.info(f"Text search triggered by user {message.from_user.id}")
    await state.set_state(UserStates.waiting_for_manga_query)
    await message.answer("Введите название манги для поиска:")


@router.message(UserStates.waiting_for_manga_query)
async def manga_search_handler(message: Message, state: FSMContext):
    logger.info(f"Search handler triggered with query: {message.text}")
    query = message.text.strip()
    if not query:
        await message.answer("Введите название для поиска")
        return

    await state.clear()

    async with get_db() as db:
        service = MangaService(db)
        try:
            logger.info(f"Starting search for: {query}")
            results = await service.search(query)
            logger.info(f"Search returned {len(results)} results")

            if not results:
                await message.answer("Манга не найдена. Попробуйте другой запрос.")
                return

            results_data = [
                {"id": str(idx), "title": r.title, "cover_url": r.cover_url, "real_id": r.id}
                for idx, r in enumerate(results)
            ]

            await state.update_data(manga_mapping={str(idx): r.id for idx, r in enumerate(results)})

            await message.answer(
                f"🔍 Результаты поиска по '{query}':",
                reply_markup=get_search_keyboard(results_data)
            )
        except Exception as e:
            logger.error(f"Error in search handler: {e}", exc_info=True)
            await message.answer("Произошла ошибка при поиске. Попробуйте позже.")
        finally:
            await service.close()


@router.callback_query(F.data.startswith("manga_card:"))
async def manga_card_callback(callback: CallbackQuery, state: FSMContext):
    idx = callback.data.split(":")[1]

    data = await state.get_data()
    manga_mapping = data.get("manga_mapping", {})
    manga_id = manga_mapping.get(idx)

    if not manga_id:
        await callback.answer("Манга не найдена")
        return

    async with get_db() as db:
        service = MangaService(db)
        try:
            manga = await service.get_title_details(manga_id)

            if not manga:
                await callback.answer("Манга не найдена")
                return

            cover_text = f"📖 <b>{manga.title}</b>\n\n"

            if manga.description:
                desc = BeautifulSoup(manga.description, "html.parser").get_text()
                desc = desc[:300] + "..." if len(desc) > 300 else desc
                cover_text += f"<i>{desc}</i>\n\n"

            if manga.year:
                cover_text += f"📅 Год: {manga.year}\n"
            if manga.status:
                cover_text += f"📌 Статус: {manga.status}\n"
            if manga.chapters_count:
                cover_text += f"📚 Глав: {manga.chapters_count}\n"

            if manga.cover_url:
                try:
                    await callback.message.answer_photo(
                        photo=manga.cover_url,
                        caption=cover_text,
                        reply_markup=get_manga_card_keyboard(manga_id)
                    )
                except Exception as e:
                    logger.error(f"Failed to send cover: {e}")
                    await callback.message.answer(
                        cover_text,
                        reply_markup=get_manga_card_keyboard(manga_id)
                    )
            else:
                await callback.message.answer(
                    cover_text,
                    reply_markup=get_manga_card_keyboard(manga_id)
                )
        finally:
            await service.close()

    await callback.answer()


@router.callback_query(F.data == "manga_search")
async def manga_search_callback(callback: CallbackQuery, state: FSMContext):
    logger.info(f"manga_search callback triggered by user {callback.from_user.id}")
    await state.set_state(UserStates.waiting_for_manga_query)
    await callback.message.answer("Введите название манги для поиска:")
    await callback.answer()
