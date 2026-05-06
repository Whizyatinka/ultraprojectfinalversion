from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔍 Поиск манги", callback_data="manga_search")
    builder.button(text="📊 Статистика", callback_data="stats")
    builder.button(text="❓ Помощь", callback_data="help")
    
    builder.adjust(1)
    return builder.as_markup()


def get_manga_card_keyboard(manga_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📥 Скачать всё", callback_data=f"manga_download_all:{manga_id}")
    builder.button(text="📖 По главам", callback_data=f"manga_by_chapter:{manga_id}")
    builder.button(text="📚 По томам", callback_data=f"manga_by_volume:{manga_id}")
    builder.button(text="🔙 Назад", callback_data="manga_search")
    
    builder.adjust(1)
    return builder.as_markup()


async def get_manga_chapters_keyboard(chapters: list, manga_id: str, user_id: int, db, page: int = 0, per_page: int = 20) -> InlineKeyboardMarkup:
    from app.utils.callback_manager import CallbackManager
    
    builder = InlineKeyboardBuilder()
    
    start = page * per_page
    end = start + per_page
    page_chapters = chapters[start:end]
    
    for ch in page_chapters:
        ch_num = ch.get("number", "?")
        ch_name = ch.get("name", "")
        display_name = f"Глава {ch_num}" + (f" - {ch_name[:20]}" if ch_name else "")
        
        # Создаем короткий callback через БД
        short_id = await CallbackManager.create_callback(
            db, user_id, "chapter",
            {"manga_id": manga_id, "chapter_id": ch.get("id"), "number": ch_num, "name": ch_name}
        )
        
        builder.button(text=display_name, callback_data=f"ch:{short_id}")
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"manga_chapters:{manga_id}:{page-1}"))
    if end < len(chapters):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"manga_chapters:{manga_id}:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.adjust(1)
    
    return builder.as_markup()


async def get_manga_volumes_keyboard(volumes: list, manga_id: str, user_id: int, db, page: int = 0, per_page: int = 20) -> InlineKeyboardMarkup:
    from app.utils.callback_manager import CallbackManager
    
    builder = InlineKeyboardBuilder()
    
    start = page * per_page
    end = start + per_page
    page_volumes = volumes[start:end]
    
    for vol in page_volumes:
        vol_num = vol.get("number", "?")
        ch_count = vol.get("chapters", 0)
        display_name = f"📖 Том {vol_num} ({ch_count} глав)"
        
        # Создаем короткий callback через БД
        short_id = await CallbackManager.create_callback(
            db, user_id, "volume",
            {"manga_id": manga_id, "volume_num": vol_num}
        )
        
        builder.button(text=display_name, callback_data=f"vol:{short_id}")
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"manga_volumes:{manga_id}:{page-1}"))
    if end < len(volumes):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"manga_volumes:{manga_id}:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.button(text="🔙 К манге", callback_data=f"manga_card:{manga_id}")
    builder.adjust(1)
    
    return builder.as_markup()


async def get_volume_chapters_keyboard(chapters: list, manga_id: str, volume_num: int, user_id: int, db) -> InlineKeyboardMarkup:
    from app.utils.callback_manager import CallbackManager
    
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Скачать весь том"
    vol_short_id = await CallbackManager.create_callback(
        db, user_id, "volume_download",
        {"manga_id": manga_id, "volume_num": volume_num, "chapters": chapters}
    )
    builder.button(
        text=f"📥 Скачать весь том {volume_num}",
        callback_data=f"vdl:{vol_short_id}"
    )
    
    # Главы тома
    for ch in chapters:
        ch_num = ch.get("number", "?")
        ch_name = ch.get("name", "")
        display_name = f"Глава {ch_num}" + (f" - {ch_name[:20]}" if ch_name else "")
        
        short_id = await CallbackManager.create_callback(
            db, user_id, "chapter",
            {"manga_id": manga_id, "chapter_id": ch.get("id"), "number": ch_num, "name": ch_name}
        )
        
        builder.button(text=display_name, callback_data=f"ch:{short_id}")
    
    builder.button(text="🔙 К манге", callback_data=f"manga_card:{manga_id}")
    builder.adjust(1)
    
    return builder.as_markup()


def get_search_keyboard(results: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in results[:10]:
        text = item.get("title", "Unknown")[:50]
        callback = f"manga_card:{item.get('id')}"
        builder.button(text=text, callback_data=callback)

    builder.button(text="🔄 Новый поиск", callback_data="manga_search")
    builder.adjust(1)
    return builder.as_markup()
