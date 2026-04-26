import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from app.models.database import get_db
from app.keyboards.inline import get_manga_chapters_keyboard, get_manga_volumes_keyboard, get_volume_chapters_keyboard
from app.services.manga_service import MangaService
from app.utils.callback_manager import CallbackManager

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith("manga_by_chapter:"))
async def manga_chapters_callback(callback: CallbackQuery, state: FSMContext):
    manga_id = callback.data.split(":")[1]
    
    async for db in get_db():
        service = MangaService(db)
        try:
            chapters = await service.get_chapters(manga_id)
            
            if not chapters:
                await callback.answer("Главы не найдены")
                return
            
            # Сортируем главы по номеру (от первой к последней)
            chapters = sorted(chapters, key=lambda x: x.number)
            
            chapters_data = [
                {"id": ch.id, "number": ch.number, "name": ch.name}
                for ch in chapters
            ]
            
            # Создаем клавиатуру с короткими callback через БД
            keyboard = await get_manga_chapters_keyboard(
                chapters_data, manga_id, callback.from_user.id, db
            )
            
            await callback.message.answer(
                f"📄 Выберите главу ({len(chapters)} глав всего):",
                reply_markup=keyboard
            )
        finally:
            await service.close()
        break
    
    await callback.answer()


@router.callback_query(F.data.startswith("manga_chapters:"))
async def manga_chapters_page_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    manga_id = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0
    
    async for db in get_db():
        service = MangaService(db)
        try:
            chapters = await service.get_chapters(manga_id)
            
            if not chapters:
                await callback.answer("Главы не найдены")
                return
            
            chapters = sorted(chapters, key=lambda x: x.number)
            
            chapters_data = [
                {"id": ch.id, "number": ch.number, "name": ch.name}
                for ch in chapters
            ]
            
            keyboard = await get_manga_chapters_keyboard(
                chapters_data, manga_id, callback.from_user.id, db, page
            )
            
            await callback.message.edit_text(
                f"📄 Выберите главу ({len(chapters_data)} глав всего):",
                reply_markup=keyboard
            )
        finally:
            await service.close()
        break
    
    await callback.answer()


@router.callback_query(F.data.startswith("manga_by_volume:"))
async def manga_volumes_callback(callback: CallbackQuery, state: FSMContext):
    manga_id = callback.data.split(":")[1]
    
    async for db in get_db():
        service = MangaService(db)
        try:
            chapters = await service.get_chapters(manga_id)
            
            if not chapters:
                await callback.answer("Главы не найдены")
                return
            
            # Группируем по томам
            volumes_dict = {}
            for ch in chapters:
                if ch.volume:
                    if ch.volume not in volumes_dict:
                        volumes_dict[ch.volume] = []
                    volumes_dict[ch.volume].append(ch)
            
            if not volumes_dict:
                await callback.answer("Тома не найдены")
                return
            
            # Сохраняем тома в state для обработчика vol:
            await state.update_data(
                volumes_dict=volumes_dict,
                current_manga_id=manga_id
            )
            
            # Формируем текст с томами
            text = f"📚 Выберите том ({len(chapters)} глав всего):\n\n"
            for vol_num in sorted(volumes_dict.keys()):
                text += f"📖 Том {vol_num}: {len(volumes_dict[vol_num])} глав\n"
            
            # Сортируем тома
            volumes_data = [
                {"number": vol_num, "chapters": len(vol_chapters)}
                for vol_num, vol_chapters in sorted(volumes_dict.items())
            ]
            
            keyboard = await get_manga_volumes_keyboard(
                volumes_data, manga_id, callback.from_user.id, db
            )
            
            await callback.message.answer(text, reply_markup=keyboard)
        finally:
            await service.close()
        break
    
    await callback.answer()


@router.callback_query(F.data.startswith("manga_volumes:"))
async def manga_volumes_page_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    manga_id = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0
    
    # Получаем данные из state
    data = await state.get_data()
    volumes_dict = data.get("volumes_dict", {})
    
    if not volumes_dict:
        await callback.answer("Данные не найдены. Попробуйте выбрать 'По томам' снова.")
        return
    
    # Формируем текст с томами
    total_chapters = sum(len(chs) for chs in volumes_dict.values())
    text = f"📚 Выберите том ({total_chapters} глав всего):\n\n"
    for vol_num in sorted(volumes_dict.keys()):
        text += f"📖 Том {vol_num}: {len(volumes_dict[vol_num])} глав\n"
    
    volumes_data = [
        {"number": vol_num, "chapters": len(vol_chapters)}
        for vol_num, vol_chapters in sorted(volumes_dict.items())
    ]
    
    async for db in get_db():
        keyboard = await get_manga_volumes_keyboard(
            volumes_data, manga_id, callback.from_user.id, db, page
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        break
    
    await callback.answer()


@router.callback_query(F.data.startswith("vol:"))
async def manga_volume_chapters_callback(callback: CallbackQuery, state: FSMContext):
    short_id = callback.data.split(":")[1]
    
    async for db in get_db():
        # Получаем данные из БД
        data = await CallbackManager.get_callback_data(db, short_id, callback.from_user.id)
        
        if not data:
            await callback.answer("Данные не найдены")
            return
        
        manga_id = data.get("manga_id")
        volume_num = data.get("volume_num")
        
        # Получаем данные из state
        state_data = await state.get_data()
        volumes_dict = state_data.get("volumes_dict", {})
        
        if not volumes_dict or volume_num not in volumes_dict:
            await callback.answer("Главы не найдены")
            return
        
        volume_chapters = sorted(volumes_dict[volume_num], key=lambda x: x.number)
        
        chapters_data = [
            {"id": ch.id, "number": ch.number, "name": ch.name}
            for ch in volume_chapters
        ]
        
        keyboard = await get_volume_chapters_keyboard(
            chapters_data, manga_id, volume_num, callback.from_user.id, db
        )
        
        await callback.message.answer(
            f"📖 Том {volume_num} ({len(volume_chapters)} глав):",
            reply_markup=keyboard
        )
        break
    
    await callback.answer()


@router.callback_query(F.data.startswith("ch:"))
async def manga_chapter_download_callback(callback: CallbackQuery, state: FSMContext):
    short_id = callback.data.split(":")[1]
    
    async for db in get_db():
        # Получаем данные из БД
        data = await CallbackManager.get_callback_data(db, short_id, callback.from_user.id)
        
        if not data:
            await callback.answer("Данные не найдены")
            return
        
        manga_id = data.get("manga_id")
        chapter_id = data.get("chapter_id")
        chapter_num = data.get("number")
        
        service = MangaService(db)
        try:
            manga = await service.get_title_details(manga_id)
            if not manga:
                await callback.message.answer("Манга не найдена")
                return
            
            # Проверяем, была ли глава уже скачана
            already_downloaded = await service.is_chapter_downloaded(
                callback.from_user.id, manga_id, chapter_id
            )
            
            if already_downloaded:
                await callback.message.answer(f"✅ Глава {chapter_num} уже была скачана ранее")
                await callback.answer()
                return
            
            await callback.message.answer("⏳ Скачиваю главу...")
            
            filepath, is_cached = await service.download_chapter(
                chapter_id, manga_id, manga.title, chapter_num, callback.from_user.id
            )
            
            if filepath:
                # Используем FSInputFile для отправки файла
                document = FSInputFile(filepath)
                await callback.message.answer_document(
                    document,
                    caption=f"📄 {manga.title} - Глава {chapter_num}"
                )
                
                await service.update_user_stats(callback.from_user.id, 1)
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            await callback.message.answer(f"❌ Ошибка при скачивании: {str(e)}")
        finally:
            await service.close()
        break
    
    await callback.answer()


@router.callback_query(F.data.startswith("vdl:"))
async def manga_volume_download_callback(callback: CallbackQuery, state: FSMContext):
    short_id = callback.data.split(":")[1]
    
    async for db in get_db():
        # Получаем данные из БД
        data = await CallbackManager.get_callback_data(db, short_id, callback.from_user.id)
        
        if not data:
            await callback.answer("Данные не найдены")
            return
        
        manga_id = data.get("manga_id")
        volume_num = data.get("volume_num")
        chapters = data.get("chapters", [])
        
        await callback.message.answer(f"⏳ Скачиваю том {volume_num}...")
        
        service = MangaService(db)
        try:
            manga = await service.get_title_details(manga_id)
            if not manga:
                await callback.message.answer("Манга не найдена")
                return
            
            await callback.message.answer(f"📥 Скачиваю {len(chapters)} глав тома {volume_num}...")
            
            downloaded = 0
            for ch in chapters:
                try:
                    filepath, _ = await service.download_chapter(
                        ch.get("id"), manga.title, ch.get("number")
                    )
                    document = FSInputFile(filepath)
                    await callback.message.answer_document(
                        document,
                        caption=f"📄 {manga.title} - Том {volume_num}, Глава {ch.get('number')}"
                    )
                    downloaded += 1
                except Exception as e:
                    logger.error(f"Error downloading chapter {ch.get('id')}: {e}")
            
            await callback.message.answer(f"✅ Скачано {downloaded} глав из тома {volume_num}")
            await service.update_user_stats(callback.from_user.id, downloaded)
            
        except Exception as e:
            logger.error(f"Volume download error: {e}")
            await callback.message.answer(f"❌ Ошибка при скачивании: {str(e)}")
        finally:
            await service.close()
        break
    
    await callback.answer()


@router.callback_query(F.data.startswith("manga_download_all:"))
async def manga_download_all_callback(callback: CallbackQuery):
    manga_id = callback.data.split(":")[1]
    
    async for db in get_db():
        service = MangaService(db)
        try:
            manga = await service.get_title_details(manga_id)
            if not manga:
                await callback.message.answer("Манга не найдена")
                return
            
            await callback.message.answer(
                f"⏳ Начинаю скачивание всех глав манги '{manga.title}'...\n"
                "Это может занять некоторое время."
            )
            
            paths = await service.download_all_chapters(manga_id, callback.from_user.id)
            
            if paths:
                await callback.message.answer(f"✅ Скачано {len(paths)} глав!")
                await service.update_user_stats(callback.from_user.id, len(paths))
            else:
                await callback.message.answer("❌ Не удалось скачать главы")
                
        except Exception as e:
            logger.error(f"Download all error: {e}")
            await callback.message.answer(f"❌ Ошибка: {str(e)}")
        finally:
            await service.close()
        break
    
    await callback.answer()


@router.callback_query(F.data == "stats")
async def stats_callback(callback: CallbackQuery):
    tg_id = callback.from_user.id
    
    async for db in get_db():
        from sqlalchemy import select
        from app.models.database import User, UserStats
        
        result = await db.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.message.answer("Вы еще ничего не скачивали.")
        else:
            stats = user.stats
            await callback.message.answer(
                f"📊 <b>Ваша статистика:</b>\n\n"
                f"📚 <b>Манга:</b> {stats.manga_chapters_count if stats else 0} глав"
            )
        break
    
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.message.answer(
        "📖 <b>Инструкция по использованию:</b>\n\n"
        "1. <b>Поиск манги</b> - найдите мангу на Remanga и скачайте главы\n"
        "2. <b>Статистика</b> - посмотрите сколько глав вы скачали\n\n"
        "⏱️ Файлы манги конвертируются в PDF, большие файлы сжимаются."
    )
    await callback.answer()
