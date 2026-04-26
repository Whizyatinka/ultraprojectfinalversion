import asyncio
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User, UserStats, DownloadedChapter
from app.services.parsers.remanga import RemangaParser, MangaTitleInfo, ChapterInfo
from app.utils.file_handler import FileHandler

logger = logging.getLogger(__name__)


class MangaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = RemangaParser()
        self.file_handler = FileHandler()
    
    async def close(self):
        await self.parser.close()
    
    async def search(self, query: str, limit: int = 10) -> list[MangaTitleInfo]:
        return await self.parser.search(query, limit)
    
    async def get_title_details(self, manga_id: str) -> Optional[MangaTitleInfo]:
        return await self.parser.get_title(manga_id)
    
    async def get_chapters(self, manga_id: str) -> list[ChapterInfo]:
        return await self.parser.get_chapters(manga_id)
    
    async def is_chapter_downloaded(self, user_id: int, manga_id: str, chapter_id: str) -> bool:
        """Проверяет, была ли глава уже скачана пользователем"""
        result = await self.db.execute(
            select(DownloadedChapter).where(
                DownloadedChapter.user_id == user_id,
                DownloadedChapter.manga_id == manga_id,
                DownloadedChapter.chapter_id == chapter_id
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def mark_chapter_downloaded(self, user_id: int, manga_id: str, chapter_id: str, chapter_number: float):
        """Отмечает главу как скачанную"""
        downloaded = DownloadedChapter(
            user_id=user_id,
            manga_id=manga_id,
            chapter_id=chapter_id,
            chapter_number=chapter_number
        )
        self.db.add(downloaded)
        await self.db.commit()
    
    async def _download_chapter(self, chapter_id: str) -> str:
        pages = await self.parser.get_chapter_pages(chapter_id)
        
        if not pages:
            raise Exception(f"No pages found for chapter {chapter_id}")
        
        logger.info(f"Downloading {len(pages)} pages for chapter {chapter_id}")
        
        temp_images = []
        for page in pages:
            try:
                logger.info(f"Downloading page {page.number}: {page.image_url}")
                img_data = await self.parser.download_image(page.image_url)
                temp_path = await self.file_handler.save_temp_file(
                    img_data, f"page_{page.number}.jpg"
                )
                temp_images.append(temp_path)
            except Exception as e:
                logger.error(f"Failed to download page {page.number}: {e}")
        
        if not temp_images:
            raise Exception(f"Failed to download any pages for chapter {chapter_id}")
        
        logger.info(f"Creating PDF from {len(temp_images)} images")
        pdf_path = await self.file_handler.images_to_pdf(
            temp_images, f"chapter_{chapter_id}.pdf"
        )
        
        await self.file_handler.cleanup_temp_files(temp_images)
        
        return pdf_path
    
    async def download_chapter(self, chapter_id: str, manga_id: str, manga_title: str, chapter_num: float, user_id: int) -> tuple[str, bool]:
        """
        Скачивает главу. Возвращает (путь_к_файлу, уже_была_скачана)
        """
        # Проверяем, была ли глава уже скачана
        already_downloaded = await self.is_chapter_downloaded(user_id, manga_id, chapter_id)
        
        if already_downloaded:
            logger.info(f"Chapter {chapter_id} already downloaded by user {user_id}, skipping...")
            return None, True
        
        # Скачиваем главу
        pdf_path = await self._download_chapter(chapter_id)
        
        # Отмечаем как скачанную
        await self.mark_chapter_downloaded(user_id, manga_id, chapter_id, chapter_num)
        
        return pdf_path, False
    
    async def download_all_chapters(self, manga_id: str, user_tg_id: int) -> list[str]:
        chapters = await self.get_chapters(manga_id)
        downloaded_paths = []
        
        semaphore = asyncio.Semaphore(3)
        
        async def download_with_limit(chapter: ChapterInfo):
            async with semaphore:
                try:
                    path = await self._download_chapter(chapter.id)
                    downloaded_paths.append(path)
                except Exception as e:
                    logger.error(f"Failed to download chapter {chapter.id}: {e}")
        
        tasks = [download_with_limit(ch) for ch in chapters]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return downloaded_paths
    
    async def update_user_stats(self, user_tg_id: int, chapters_count: int):
        result = await self.db.execute(
            select(UserStats).where(UserStats.user_id == user_tg_id)
        )
        stats = result.scalar_one_or_none()
        
        if not stats:
            stats = UserStats(user_id=user_tg_id, manga_chapters_count=chapters_count)
            self.db.add(stats)
        else:
            stats.manga_chapters_count += chapters_count
        
        await self.db.commit()
