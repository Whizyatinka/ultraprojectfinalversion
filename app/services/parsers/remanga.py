import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from app.config import config

logger = logging.getLogger(__name__)


@dataclass
class MangaTitleInfo:
    id: str
    title: str
    cover_url: Optional[str]
    description: Optional[str]
    year: Optional[int]
    status: Optional[str]
    chapters_count: int


@dataclass
class ChapterInfo:
    id: str
    number: float
    volume: Optional[int]
    name: Optional[str]
    pages_count: int


@dataclass
class PageInfo:
    number: int
    image_url: str


class RemangaParser:
    BASE_URL = "https://remanga.org"
    API_URL = "https://api.remanga.org/api"
    FLARESOLVERR_URL = "http://localhost:8191/v1"
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        # Remanga работает без VPN и не требует специальных заголовков
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
        logger.info("RemangaParser initialized with FlareSolverr support")
    
    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers,
                connector=aiohttp.TCPConnector(ssl=True)
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _download_with_flaresolverr(self, url: str) -> bytes:
        """Скачивает изображение через FlareSolverr для обхода Cloudflare"""
        try:
            session = await self._get_session()
            
            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000
            }
            
            logger.info(f"Using FlareSolverr for: {url}")
            async with session.post(self.FLARESOLVERR_URL, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"FlareSolverr error: {response.status}")
                
                result = await response.json()
                
                if result.get("status") != "ok":
                    raise Exception(f"FlareSolverr failed: {result.get('message')}")
                
                # FlareSolverr возвращает base64 encoded content для бинарных данных
                import base64
                solution = result.get("solution", {})
                response_text = solution.get("response")
                
                if response_text:
                    # Если это base64
                    try:
                        return base64.b64decode(response_text)
                    except:
                        return response_text.encode()
                
                raise Exception("No content in FlareSolverr response")
                
        except Exception as e:
            logger.error(f"FlareSolverr error: {e}")
            raise
    
    async def search(self, query: str, limit: int = 10) -> list[MangaTitleInfo]:
        url = f"{self.API_URL}/search/"
        params = {"query": query}
        
        try:
            logger.info(f"Searching manga: '{query}' at {url}")
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                logger.info(f"Response status: {response.status}")
                
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Remanga search failed with status {response.status}, body: {text[:200]}")
                    return []
                
                data = await response.json()
                logger.info(f"Response data keys: {data.keys()}")
                results = []
                
                items = data.get("content", [])
                logger.info(f"Number of items in data: {len(items)}")
                
                for item in items[:limit]:
                    # Используем dir как ID (т.к. ID не работает)
                    manga_dir = item.get("dir", "")
                    results.append(MangaTitleInfo(
                        id=manga_dir,  # Используем dir вместо id
                        title=item.get("rus_name") or item.get("en_name", "Unknown"),
                        cover_url=f"https://remanga.org{item.get('img', {}).get('high')}" if item.get("img", {}).get("high") else None,
                        description=None,  # В поиске нет описания
                        year=item.get("issue_year"),
                        status=item.get("status", {}).get("name") if isinstance(item.get("status"), dict) else None,
                        chapters_count=item.get("count_chapters", 0)
                    ))
                
                logger.info(f"Found {len(results)} manga for query '{query}'")
                return results
        except Exception as e:
            logger.error(f"Remanga search error: {type(e).__name__}: {e}", exc_info=True)
            return []
    
    async def get_title(self, manga_id: str) -> Optional[MangaTitleInfo]:
        # manga_id это dir (например "naruto")
        url = f"{self.API_URL}/titles/{manga_id}/"
        
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to get title {manga_id}, status: {response.status}")
                    return None
                
                data = await response.json()
                item = data.get("content", {})
                
                return MangaTitleInfo(
                    id=item.get("dir", manga_id),
                    title=item.get("rus_name") or item.get("en_name", "Unknown"),
                    cover_url=f"https://remanga.org{item.get('img', {}).get('high')}" if item.get("img", {}).get("high") else None,
                    description=item.get("description"),
                    year=item.get("issue_year"),
                    status=item.get("status", {}).get("name") if isinstance(item.get("status"), dict) else None,
                    chapters_count=item.get("count_chapters", 0)
                )
        except Exception as e:
            logger.error(f"Remanga get_title error: {e}")
            return None
    
    async def get_chapters(self, manga_id: str, volume: Optional[int] = None) -> list[ChapterInfo]:
        # Сначала получаем тайтл, чтобы узнать branch_id
        title = await self.get_title(manga_id)
        if not title:
            logger.error(f"Cannot get title for {manga_id}")
            return []
        
        # Получаем branch_id из тайтла
        title_url = f"{self.API_URL}/titles/{manga_id}/"
        session = await self._get_session()
        
        try:
            async with session.get(title_url) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                branches = data.get("content", {}).get("branches", [])
                
                if not branches:
                    logger.error(f"No branches found for {manga_id}")
                    return []
                
                branch_id = branches[0]["id"]
                
                # Загружаем ВСЕ главы с пагинацией
                all_chapters = []
                page = 1
                
                while True:
                    chapters_url = f"{self.API_URL}/titles/chapters/"
                    params = {"branch_id": branch_id, "ordering": "index", "page": page, "count": 100}
                    
                    async with session.get(chapters_url, params=params) as ch_response:
                        if ch_response.status != 200:
                            break
                        
                        ch_data = await ch_response.json()
                        content = ch_data.get("content", [])
                        
                        if not content:
                            break
                        
                        for item in content:
                            all_chapters.append(ChapterInfo(
                                id=str(item.get("id", "")),
                                number=float(item.get("chapter", 0)),
                                volume=item.get("tome"),
                                name=item.get("name"),
                                pages_count=item.get("pages", 0)
                            ))
                        
                        # Проверяем, есть ли ещё страницы
                        if len(content) < 100:
                            break
                        
                        page += 1
                
                logger.info(f"Loaded {len(all_chapters)} chapters for {manga_id}")
                return all_chapters
        except Exception as e:
            logger.error(f"Remanga get_chapters error: {e}")
            return []
    
    async def get_chapter_pages(self, chapter_id: str) -> list[PageInfo]:
        url = f"{self.API_URL}/titles/chapters/{chapter_id}/"
        
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                logger.info(f"Getting pages for chapter {chapter_id}, status: {response.status}")
                
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Failed to get chapter pages: {text[:200]}")
                    return []
                
                data = await response.json()
                logger.info(f"Chapter data keys: {data.keys()}")
                
                pages = []
                
                chapter_data = data.get("content", {})
                logger.info(f"Chapter content keys: {chapter_data.keys() if chapter_data else 'None'}")
                
                # Remanga может возвращать pages в разных форматах
                page_list = chapter_data.get("pages", [])
                
                if not page_list:
                    logger.error(f"No pages found for chapter {chapter_id}")
                    logger.error(f"Full chapter data: {chapter_data}")
                    return []
                
                logger.info(f"Found {len(page_list)} pages")
                
                for idx, page in enumerate(page_list, start=1):
                    # page может быть строкой (URL), объектом или списком
                    image_url = ""
                    
                    if isinstance(page, str):
                        image_url = page
                    elif isinstance(page, list):
                        # Remanga возвращает список объектов [{id, link, height, width}, ...]
                        if len(page) > 0:
                            first_item = page[0]
                            if isinstance(first_item, dict):
                                image_url = first_item.get("link", "")
                            elif isinstance(first_item, str):
                                image_url = first_item
                    elif isinstance(page, dict):
                        image_url = page.get("link") or page.get("url") or page.get("image", "")
                    else:
                        logger.warning(f"Unknown page format: {type(page)}, value: {page}")
                        continue
                    
                    if image_url:
                        # Убираем пробелы и другие недопустимые символы
                        image_url = image_url.strip()
                        
                        # Добавляем базовый URL если нужно
                        if not image_url.startswith("http"):
                            image_url = f"https://remanga.org{image_url}"
                        
                        logger.info(f"Page {idx} URL: {image_url}")
                        
                        pages.append(PageInfo(
                            number=idx,
                            image_url=image_url
                        ))
                
                logger.info(f"Returning {len(pages)} pages for chapter {chapter_id}")
                return pages
        except Exception as e:
            logger.error(f"Remanga get_chapter_pages error: {e}", exc_info=True)
            return []
    
    async def download_image(self, url: str, retry_count: int = 2) -> bytes:
        # Добавляем небольшую задержку для избежания блокировки
        await asyncio.sleep(0.3)
        
        # Сначала пробуем обычный способ
        for attempt in range(retry_count):
            try:
                session = await self._get_session()
                
                image_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://remanga.org/",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                }
                
                async with session.get(url, headers=image_headers, allow_redirects=True) as response:
                    logger.info(f"Downloading image (attempt {attempt + 1}): {url}, status: {response.status}")
                    
                    if response.status == 403:
                        # Cloudflare блокировка - используем FlareSolverr
                        logger.warning(f"Got 403, switching to FlareSolverr...")
                        return await self._download_with_flaresolverr(url)
                    
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"Failed to download image, status {response.status}: {text[:200]}")
                        
                        if attempt < retry_count - 1:
                            await asyncio.sleep(2)
                            continue
                        
                        raise Exception(f"Failed to download image from {url}, status: {response.status}")
                    
                    content = await response.read()
                    logger.info(f"Downloaded {len(content)} bytes")
                    return content
            except Exception as e:
                if "403" in str(e) or "Cloudflare" in str(e):
                    # Пробуем FlareSolverr
                    logger.warning(f"Switching to FlareSolverr due to: {e}")
                    try:
                        return await self._download_with_flaresolverr(url)
                    except Exception as fs_error:
                        logger.error(f"FlareSolverr also failed: {fs_error}")
                        raise
                
                if attempt == retry_count - 1:
                    logger.error(f"Remanga download_image error after {retry_count} attempts: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                await asyncio.sleep(2)
