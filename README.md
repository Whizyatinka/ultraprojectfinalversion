# Telegram бот для скачивания манги (Remanga)

## Общее описание

Это асинхронный Telegram-бот на Python, который позволяет пользователям искать и скачивать мангу с сайта **remanga.org** в формате PDF. Бот построен на фреймворке **aiogram 3.x**, использует **SQLAlchemy 2.0** для работы с базой данных и поддерживает как SQLite, так и PostgreSQL.

Ключевая особенность — обход защиты Cloudflare при скачивании изображений через комбинацию `cloudscraper` + `aiohttp` с реалистичными HTTP-заголовками.

---

## Архитектура и поток данных

```
Пользователь (Telegram)
    ↓
aiogram Dispatcher (app/loader.py)
    ↓
Router'ы обработчиков (app/handlers/)
    ↓
Клавиатуры (app/keyboards/inline.py)
    ↓
MangaService (app/services/manga_service.py)
    ↓
RemangaParser (app/services/parsers/remanga.py) ←→ HTTP API remanga.org
    ↓
FileHandler (app/utils/file_handler.py) — создание PDF
    ↓
Telegram API — отправка документа пользователю
    ↓
SQLAlchemy ORM (app/models/database.py) — сохранение статистики и истории
```

---

## Описание каждого файла

### Корневые файлы

#### `run_bot.py`
**Назначение:** точка входа в приложение.

```python
os.chdir('F:/telegram-bot')
sys.path.insert(0, 'F:/telegram-bot')
```

- Переключает рабочую директорию на `F:/telegram-bot` (жёстко закодирован путь для Windows)
- Добавляет путь проекта в `sys.path`, чтобы импорты `app.*` работали корректно
- Вызывает `asyncio.run(main())`, который запускает `Loader.start()`

**Зачем нужен:** без него при запуске из другой директории Python не найдёт пакет `app`.

---

#### `start_bot.bat`
**Назначение:** batch-файл для удобного запуска на Windows.

```batch
@echo off
echo Starting Telegram Bot with TUN mode...
echo Make sure Hiddify TUN mode is enabled!
python run_bot.py
pause
```

- Выводит напоминание о необходимости включения **Hiddify TUN mode** (VPN-клиент, используемый для обхода блокировок)
- Запускает `run_bot.py`
- `pause` не даёт консоли закрыться сразу после ошибки

---

#### `.env`
**Назначение:** хранение секретов и конфигурации.

```env
BOT_TOKEN=8609460139:AAHY3lbEomepYMEfDbeEE3mIRoiw9qfMRlc
POSTGRES_USER=bot_user
POSTGRES_PASSWORD=123455
POSTGRES_DB=telegram_bot
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
USE_SQLITE=true
```

| Переменная | Описание |
|-----------|----------|
| `BOT_TOKEN` | Токен бота, полученный от [@BotFather](https://t.me/botfather) |
| `POSTGRES_*` | Настройки PostgreSQL (используются только если `USE_SQLITE=false`) |
| `USE_SQLITE` | Переключатель: `true` — использовать SQLite, `false` — PostgreSQL |

**Важно:** файл `.env` не должен попадать в публичный Git-репозиторий (добавьте в `.gitignore`).

---

#### `requirements.txt`
**Назначение:** список Python-зависимостей.

| Пакет | Версия | Назначение |
|-------|--------|-----------|
| `aiogram` | >=3.0.0 | Фреймворк для Telegram Bot API |
| `sqlalchemy[asyncio]` | >=2.0.0 | Асинхронный ORM для работы с БД |
| `asyncpg` | >=0.29.0 | Асинхронный драйвер PostgreSQL |
| `alembic` | >=1.13.0 | Миграции базы данных (сейчас не используется активно) |
| `httpx` | >=0.26.0 | HTTP-клиент (резервный) |
| `httpx-socks` | >=0.9.0 | SOCKS-прокси для httpx |
| `beautifulsoup4` | >=4.12.0 | Парсинг HTML (используется для очистки описания манги от тегов) |
| `lxml` | >=5.0.0 | Быстрый XML/HTML-парсер для BeautifulSoup |
| `Pillow` | >=10.0.0 | Обработка изображений (сжатие, изменение размеров) |
| `img2pdf` | >=0.5.1 | Конвертация набора изображений в PDF |
| `python-dotenv` | >=1.0.0 | Чтение переменных из `.env` |
| `aiofiles` | >=23.2.0 | Асинхронная работа с файлами |
| `aiohttp-socks` | >=0.8.0 | SOCKS-прокси для aiohttp |
| `aiodns` | >=3.0.0 | Асинхронное DNS-разрешение |
| `brotli` | >=1.0.0 | Сжатие Brotli для HTTP |

---

#### `Dockerfile`
**Назначение:** инструкция для сборки Docker-образа.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p downloads
CMD ["python", "-m", "app.loader"]
```

- Базовый образ: Python 3.11 slim
- Устанавливаются системные зависимости (`gcc`, `libpq-dev`) для компиляции Python-пакетов
- Создаётся папка `downloads` для временных файлов
- Точка входа: `python -m app.loader` (запускает `loader.py` как модуль)

---

#### `docker-compose.yml`
**Назначение:** оркестрация двух сервисов.

```yaml
services:
  bot:
    build: .
    env_file: .env
    depends_on: postgres
    volumes: ./downloads:/app/downloads
  postgres:
    image: postgres:15-alpine
    environment: POSTGRES_*
    volumes: postgres_data:/var/lib/postgresql/data
    ports: "5432:5432"
volumes: postgres_data
```

| Сервис | Описание |
|--------|----------|
| `bot` | Сам бот, собирается из `Dockerfile`, читает `.env` |
| `postgres` | PostgreSQL 15 Alpine, данные хранятся в именованном volume |

**Примечание:** сейчас в `.env` установлено `USE_SQLITE=true`, поэтому PostgreSQL-контейнер не используется даже при `docker-compose up`.

---

#### `pyproject.toml`
**Назначение:** современный формат описания Python-проекта (PEP 518). Содержит метаданные и настройки сборки. В данном проекте используется минимально.

---

### Пакет `app/`

#### `app/__init__.py`
**Назначение:** пустой файл, обозначающий директорию `app/` как Python-пакет.

---

#### `app/loader.py`
**Назначение:** центральный загрузчик и инициализатор бота.

**Ключевые компоненты:**

**Класс `Loader`**:
- `bot: Bot` — экземпляр aiogram-бота
- `dp: Dispatcher` — диспетчер сообщений с `MemoryStorage`
- `storage: MemoryStorage` — хранилище FSM-состояний в оперативной памяти

**Метод `load()`**:
1. Создаёт `AiohttpSession` для HTTP-соединений
2. Инициализирует `Bot` с `parse_mode=ParseMode.HTML` (позволяет использовать HTML-разметку в сообщениях)
3. Инициализирует `Dispatcher` с `MemoryStorage`
4. Вызывает `init_db()` — создаёт таблицы в БД, если их нет
5. Загружает 3 роутера: `commands`, `manga`, `callbacks`

**Метод `start()`**:
1. `delete_webhook(drop_pending_updates=True)` — удаляет вебхук (на случай, если бот ранее работал через webhook) и сбрасывает накопившиеся обновления
2. `dp.start_polling(bot)` — запускает бесконечный цикл long-polling

**Метод `close()`**:
- Закрывает HTTP-сессию бота

**Почему именно `MemoryStorage`:** состояния пользователей (например, "жду ввода названия манги") хранятся в RAM. При перезапуске бота все состояния сбрасываются. Для продакшена с несколькими инстансами лучше использовать `RedisStorage`.

---

#### `app/config.py`
**Назначение:** единый источник конфигурации проекта.

```python
@dataclass
class Config:
    BOT_TOKEN: str
    POSTGRES_USER/PASSWORD/DB/HOST/PORT
    PROXY_URL: str
    MAX_FILE_SIZE_TG: int = 50 * 1024 * 1024  # 50 MB
    COMPRESSION_QUALITY: int = 85               # JPEG quality
    MAX_IMAGE_DIMENSION: int = 2000            # px
    USE_SQLITE: bool = True
```

**Логика:**
- `load_dotenv()` читает `.env` файл при импорте
- Все переменные берутся из окружения, с дефолтными значениями
- `config = Config()` — синглтон, импортируется во всех модулях

**Где используются константы:**
- `MAX_FILE_SIZE_TG` — в `callbacks.py` и `manga_service.py` для проверки размера PDF перед отправкой в Telegram
- `COMPRESSION_QUALITY` — в `file_handler.py` при сжатии изображений
- `MAX_IMAGE_DIMENSION` — ограничение разрешения картинок

---

### `app/handlers/` — обработчики сообщений

#### `app/handlers/__init__.py`
**Назначение:** импортирует 3 модуля обработчиков, чтобы `loader.py` мог подключить их через `from app.handlers import commands, manga, callbacks`.

---

#### `app/handlers/commands.py`
**Назначение:** обработка текстовых команд бота.

**Класс `UserStates(StatesGroup)`**:
```python
waiting_for_manga_query = State()
```
Единственное состояние FSM — ожидание ввода названия манги от пользователя.

**Обработчики:**

| Декоратор | Функция | Описание |
|-----------|---------|----------|
| `@router.message(Command("start"))` | `cmd_start()` | Отправляет приветствие и главное меню (inline-кнопки: Поиск, Статистика, Помощь). Сбрасывает текущее состояние FSM. |
| `@router.message(Command("help"))` | `cmd_help()` | Инструкция по использованию бота. |
| `@router.message(Command("stats"))` | `cmd_stats()` | Запрашивает из БД таблицы `users` и `user_stats`, показывает сколько глав скачал пользователь. |

**Особенность `cmd_stats()`:**
- Использует `async for db in get_db():` — генератор сессий SQLAlchemy
- `scalar_one_or_none()` — безопасное получение одной записи (не падает, если записи нет)
- `relationship("UserStats")` позволяет обращаться к статистике через `user.stats`

---

#### `app/handlers/manga.py`
**Назначение:** обработка поиска манги и отображения карточек.

**`manga_search_start()`**:
- Триггер: пользователь нажимает кнопку **"🔍 Поиск манги"** (либо пишет точный текст)
- Устанавливает состояние `waiting_for_manga_query`
- Просит ввести название манги

**`manga_search_handler()`**:
- Триггер: пользователь ввёл текст в состоянии `waiting_for_manga_query`
- Очищает состояние (`state.clear()`)
- Вызывает `MangaService.search(query)`
- **Маппинг результатов:** создаёт массив с индексами `0..9`, но сохраняет в `state` маппинг `idx → real_id` (поле `dir` из API Remanga). Это нужно, потому что callback_data в Telegram ограничен 64 байтами, и нельзя передавать длинные ID напрямую.
- Отправляет сообщение с inline-клавиатурой из `get_search_keyboard()`

**`manga_card_callback()`**:
- Триггер: нажатие кнопки с результатом поиска (`manga_card:{idx}`)
- Достаёт реальный `manga_id` из FSM-state по индексу
- Вызывает `MangaService.get_title_details(manga_id)`
- Формирует карточку: название, описание (очищенное от HTML через `BeautifulSoup`), год, статус, количество глав
- Пытается отправить с обложкой (`answer_photo`); при неудаче — текстом
- Прикрепляет клавиатуру карточки: "Скачать всё", "По главам", "По томам", "Назад"

**`manga_search_callback()`**:
- Триггер: кнопка **"🔙 Назад"** или **"🔄 Новый поиск"**
- Возвращает в режим ввода названия манги

---

#### `app/handlers/callbacks.py`
**Назначение:** обработка ВСЕХ inline-кнопок (самый большой файл, 450 строк).

**`manga_chapters_callback()`** — `manga_by_chapter:{manga_id}`:
- Получает список глав через `service.get_chapters()`
- Сортирует по номеру главы (`sorted(chapters, key=lambda x: x.number)`)
- Формирует `chapters_data` — список словарей с `id`, `number`, `name`
- Создаёт клавиатуру через `get_manga_chapters_keyboard()` с **короткими callback_id** (сохраняются в БД через `CallbackManager`)
- Постраничная навигация: по 20 глав на страницу

**`manga_volumes_callback()`** — `manga_by_volume:{manga_id}`:
- Получает главы, группирует по полю `volume` (том)
- Сохраняет `volumes_dict` в FSM-state (нужно для последующей навигации)
- Формирует список томов с количеством глав в каждом

**`manga_volume_chapters_callback()`** — `vol:{short_id}`:
- Достаёт `manga_id` и `volume_num` из `CallbackManager` по короткому ID
- Получает `volumes_dict` из FSM-state
- Формирует клавиатуру глав конкретного тома + кнопка "Скачать весь том"

**`manga_chapter_download_callback()`** — `ch:{short_id}` (самый сложный обработчик):
1. Достаёт данные главы из `CallbackManager`
2. Получает детали манги (`get_title_details`)
3. **Проверяет, не скачана ли глава:** `is_chapter_downloaded()`
4. Если уже скачана — сообщает пользователю и выходит
5. Отправляет сообщение с прогресс-баром: `▱▱▱▱▱▱▱▱▱▱ 0%`
6. Определяет функцию `update_progress(current, total, status)`:
   - `"downloading"` — обновляет прогресс-бар в сообщении
   - `"creating_pdf"` — меняет текст на "Создаю PDF..."
7. Вызывает `service.download_chapter()` с `progress_callback`
8. Удаляет сообщение с прогрессом
9. Проверяет размер файла:
   - `> 50 MB` — предупреждение (Telegram не принимает)
   - `< 50 MB` — отправляет через `FSInputFile` с подписью
10. Обновляет статистику пользователя

**`manga_volume_download_callback()`** — `vdl:{short_id}`:
- Скачивает все главы тома последовательно
- Для каждой главы проверяет размер, пропускает если >50 MB
- В конце сообщает, сколько глав успешно скачано

**`manga_download_all_callback()`** — `manga_download_all:{manga_id}`:
- Вызывает `service.download_all_chapters()`
- Использует `asyncio.Semaphore(3)` — максимум 3 параллельных скачивания
- Отправляет общее количество скачанных глав

**`stats_callback()` / `help_callback()`** — inline-варианты команд `/stats` и `/help`.

---

### `app/keyboards/` — генераторы клавиатур

#### `app/keyboards/__init__.py`
**Назначение:** пустой файл, обозначающий пакет.

---

#### `app/keyboards/inline.py`
**Назначение:** создание всех inline-клавиатур бота.

**`get_main_menu_keyboard()`**:
- 3 кнопки в один столбец (`adjust(1)`): 🔍 Поиск манги, 📊 Статистика, ❓ Помощь

**`get_manga_card_keyboard(manga_id)`**:
- 📥 Скачать всё (`manga_download_all:{id}`)
- 📖 По главам (`manga_by_chapter:{id}`)
- 📚 По томам (`manga_by_volume:{id}`)
- 🔙 Назад (`manga_search`)

**`get_manga_chapters_keyboard()`**:
- **Асинхронная функция** — принимает `db` для сохранения callback-данных
- Для каждой главы создаёт короткий ID через `CallbackManager.create_callback()`
- Текст кнопки: `Глава {number} - {name[:20]}`
- Callback: `ch:{short_id}` (всего ~19 символов, укладывается в лимит Telegram)
- Навигация: ⬅️ Назад / Вперёд ➡️ при наличии других страниц
- `per_page=20` — 20 глав на страницу

**`get_manga_volumes_keyboard()`**:
- Аналогично главам, но для томов
- Callback: `vol:{short_id}`

**`get_volume_chapters_keyboard()`**:
- Первая кнопка: **"📥 Скачать весь том N"** (тип `volume_download`)
- Далее — список глав тома (тип `chapter`)
- В конце: 🔙 К манге

**`get_search_keyboard()`**:
- До 10 кнопок-результатов поиска
- Callback: `manga_card:{idx}` (индекс, не реальный ID!)
- Последняя кнопка: 🔄 Новый поиск

**Почему используется `CallbackManager`:**
Telegram ограничивает `callback_data` inline-кнопки **64 байтами**. Реальные ID глав и ID пользователей в сумме могут превышать этот лимит. Поэтому в callback передаётся 16-символьный MD5-hash, а полные данные хранятся в таблице `callback_data`.

---

### `app/models/` — модели базы данных

#### `app/models/database.py`
**Назначение:** полное определение схемы БД на SQLAlchemy 2.0 с async-режимом.

**`get_database_url()`**:
```python
if config.USE_SQLITE:
    return "sqlite+aiosqlite:///telegram_bot.db"
else:
    return "postgresql+asyncpg://..."
```

**Движок:**
```python
async_engine = create_async_engine(get_database_url(), echo=False)
async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
```

**Таблицы:**

**`User`** (`users`):
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer PK | Внутренний ID |
| `tg_id` | BigInteger unique | Telegram ID пользователя |
| `username` | String(255) | @username (может быть null) |
| `created_at` | DateTime | Дата регистрации |
| `stats` | relationship | One-to-one с `UserStats` |

**`UserStats`** (`user_stats`):
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer PK | Внутренний ID |
| `user_id` | BigInteger FK → users.tg_id | Telegram ID |
| `manga_chapters_count` | Integer | Сколько глав скачано всего |

**`CallbackData`** (`callback_data`):
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer PK | Внутренний ID |
| `short_id` | String(32) unique index | MD5-hash для callback-кнопки |
| `user_id` | BigInteger index | Telegram ID (изоляция по пользователю) |
| `data_type` | String(32) | Тип: 'chapter', 'volume', 'volume_download' |
| `full_data` | Text | Полные данные в формате JSON |
| `created_at` | DateTime | Дата создания |

**`DownloadedChapter`** (`downloaded_chapters`):
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer PK | Внутренний ID |
| `user_id` | BigInteger index | Кто скачал |
| `manga_id` | String(255) | ID манги (dir из Remanga) |
| `chapter_id` | String(255) | ID главы |
| `chapter_number` | Float | Номер главы |
| `downloaded_at` | DateTime | Когда скачал |

**`get_db()`**:
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```
Асинхронный генератор сессий. Используется как `async for db in get_db():` в обработчиках. Сессия автоматически закрывается после выхода из блока.

**`init_db()`**:
```python
async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```
Создаёт все таблицы при первом запуске (если их нет). Использует `run_sync`, потому что `create_all` — синхронная функция SQLAlchemy.

---

### `app/services/` — бизнес-логика

#### `app/services/manga_service.py`
**Назначение:** сервисный слой, связывающий обработчики, парсер и БД.

**`class MangaService`**:
```python
def __init__(self, db: AsyncSession):
    self.db = db
    self.parser = RemangaParser()
    self.file_handler = FileHandler()
```

**Методы:**

| Метод | Описание |
|-------|----------|
| `search(query)` | Делегирует `RemangaParser.search()` |
| `get_title_details(manga_id)` | Делегирует `RemangaParser.get_title()` |
| `get_chapters(manga_id)` | Делегирует `RemangaParser.get_chapters()` |
| `is_chapter_downloaded()` | Проверяет наличие записи в `downloaded_chapters` |
| `mark_chapter_downloaded()` | Добавляет запись в `downloaded_chapters` |

**`_download_chapter()`** (приватный):
1. Получает список страниц: `parser.get_chapter_pages(chapter_id)`
2. Для каждой страницы:
   - Скачивает через `parser.download_image()`
   - Сохраняет во временный файл через `file_handler.save_temp_file()`
   - Если `compress=True` — сжимает изображение
3. Создаёт PDF: `file_handler.images_to_pdf(temp_images, filename)`
4. Проверяет размер:
   - Если `> 50 MB` и `compress=False` → рекурсивно вызывает себя с `compress=True`
   - Удаляет временные изображения
5. Возвращает путь к PDF

**`download_chapter()`** (публичный):
1. Проверяет `is_chapter_downloaded()`
2. Если уже скачана → возвращает `(None, True)`
3. Вызывает `_download_chapter()`
4. Вызывает `mark_chapter_downloaded()`
5. Возвращает `(pdf_path, False)`

**`download_all_chapters()`**:
```python
semaphore = asyncio.Semaphore(3)
```
- Ограничивает concurrency до 3 одновременных скачиваний
- Создаёт по корутине на каждую главу
- `asyncio.gather(..., return_exceptions=True)` — выполняет все, не падает при ошибках отдельных глав

**`update_user_stats()`**:
- Ищет запись `UserStats` по `user_id`
- Если нет — создаёт новую
- Если есть — увеличивает `manga_chapters_count`
- Коммитит транзакцию

---

### `app/services/parsers/` — парсеры внешних источников

#### `app/services/parsers/remanga.py`
**Назначение:** HTTP-клиент для API remanga.org. Самый технически сложный модуль.

**Dataclasses:**

```python
@dataclass
class MangaTitleInfo:
    id: str          # dir (например "naruto")
    title: str       # rus_name или en_name
    cover_url: str   # https://remanga.org/img/high/...
    description: str # HTML-описание
    year: int        # issue_year
    status: str      # "Онгоинг", "Завершён" и т.д.
    chapters_count: int

@dataclass
class ChapterInfo:
    id: str          # chapter ID
    number: float    # номер главы
    volume: int      # номер тома
    name: str        # название главы
    pages_count: int

@dataclass
class PageInfo:
    number: int      # порядковый номер
    image_url: str   # прямой URL к изображению
```

**Константы:**
```python
BASE_URL = "https://remanga.org"
API_URL = "https://api.remanga.org/api"
FLARESOLVERR_URL = "http://localhost:8191/v1"
```

**Инициализация:**
- Создаёт `aiohttp.ClientSession` с таймаутом 30 секунд
- Устанавливает User-Agent Chrome 120
- Создаёт `cloudscraper` с эмуляцией Chrome на Windows

**`_get_session()`**:
- Ленивая инициализация сессии
- Проверяет `session.closed` (важно после ошибок)

**`_download_with_flaresolverr()`**:
- Отправляет POST на локальный FlareSolverr
- Ждёт до 60 секунд
- Обрабатывает base64-ответ
- **Резервный метод** — используется, если `cloudscraper` не справился

**`_calculate_relevance(query, title)`**:
Логика ранжирования поисковых результатов:

| Условие | Score |
|---------|-------|
| Точное совпадение | 100 |
| Название начинается с запроса | 90 |
| Запрос после пробела/дефиса | 80 |
| Запрос содержится в названии | 70 |
| Все слова запроса найдены | 60 |
| Часть слов найдена | 40–50 |
| Нет совпадений | 0 |

После вычисления результаты сортируются по убыванию score, фильтруются (score >= 40) и обрезаются до `limit`.

**`search(query)`**:
- `GET /api/search/?query={query}`
- Ответ: `{"content": [...]}`
- Использует поле `dir` как ID манги (не числовой `id`, потому что API remanga работает с slug/directory)
- Обложка: `https://remanga.org{img.high}`

**`get_title(manga_id)`**:
- `GET /api/titles/{dir}/`
- Возвращает `MangaTitleInfo` с полным описанием

**`get_chapters(manga_id)`**:
1. Сначала получает тайтл, чтобы узнать `branch_id`
2. `GET /api/titles/chapters/?branch_id={id}&ordering=index&page={N}&count=100`
3. **Пагинация:** цикл `while True`, загружает по 100 глав за запрос
4. Прекращает, когда `len(content) < 100`
5. Возвращает полный список `ChapterInfo`

**`get_chapter_pages(chapter_id)`**:
- `GET /api/titles/chapters/{chapter_id}/`
- Обрабатывает 3 формата данных в `pages`:
  1. **Строка** — прямой URL
  2. **Список** — `page[0]["link"]` (Remanga возвращает массив вариантов качества)
  3. **Словарь** — `page.get("link")` или `"url"` или `"image"`
- Добавляет `https://remanga.org` префикс, если URL относительный

**`download_image(url)`**:
Алгоритм с 3 попытками и экспоненциальной задержкой:

1. Пауза 0.5 сек (rate limiting)
2. Попытка через `aiohttp` с расширенными заголовками:
   - `Referer: https://remanga.org/`
   - `Sec-Fetch-*` — имитация браузера
   - `Accept: image/avif,image/webp,...`
3. Если `status == 200` — возвращает `bytes`
4. Если `status == 403` — переключается на `cloudscraper`
5. При ошибке — задержка `2 * (attempt + 1)` секунд
6. Если `cloudscraper` тоже падает — поднимает исключение

**`_download_with_cloudscraper()`**:
- Запускает синхронный `cloudscraper.get()` через `asyncio.to_thread()`
- `cloudscraper` сам обходит защиту Cloudflare, имитируя браузер
- Передаёт `Referer` и `Accept`

---

### `app/utils/` — вспомогательные утилиты

#### `app/utils/callback_manager.py`
**Назначение:** система сокращения callback_data для inline-кнопок Telegram.

**Проблема:** Telegram ограничивает `callback_data` **64 байтами** (примерно 64 символа ASCII). Реальные ID могут быть длиннее.

**Решение:**
1. Генерируется короткий MD5-hash из данных
2. Полные данные сохраняются в таблицу `callback_data`
3. В кнопку передаётся только 16-символьный hash

**`_generate_short_id()`**:
```python
content = f"{user_id}:{data_type}:{full_data}:{timestamp}"
return hashlib.md5(content.encode()).hexdigest()[:16]
```
- Использует `timestamp`, чтобы одинаковые данные разных пользователей получали разные ID
- Длина: 16 символов (32 hex / 2)

**`create_callback()`**:
1. Сериализует `data` в JSON
2. Генерирует `short_id`
3. Проверяет, нет ли такого ID в БД (дедупликация)
4. Создаёт запись `CallbackData`
5. Коммитит и возвращает `short_id`

**`get_callback_data()`**:
- Ищет по `short_id` И `user_id` (безопасность — пользователь не может подменить чужой callback)
- Десериализует JSON из `full_data`

**`cleanup_old_callbacks()`**:
- Удаляет callback старше N дней (по умолчанию 7)
- Предотвращает разрастание таблицы

---

#### `app/utils/file_handler.py`
**Назначение:** файловые операции: временные файлы, PDF, сжатие.

**`__init__()`**:
- Создаёт директорию `downloads/` при инициализации

**`save_temp_file(content, filename)`**:
- Асинхронная запись байтов через `aiofiles`
- Возвращает полный путь к файлу

**`images_to_pdf(image_paths, output_filename)`**:
```python
f.write(img2pdf.convert(image_paths))
```
- Использует библиотеку `img2pdf` — конвертирует список изображений в один PDF
- **Важно:** `img2pdf` не сжимает изображения, а просто упаковывает их как есть

**`compress_image(image_path, quality)`**:
1. Открывает через `PIL.Image.open()`
2. Если максимальная сторона > 2000px — уменьшает через `thumbnail()` с фильтром `LANCZOS` (высокое качество)
3. Сохраняет как JPEG с заданным качеством (по умолчанию 85, при пересоздании 70)
4. Возвращает путь к сжатому файлу

**`check_file_size(filepath)`**:
- Синхронный `os.path.getsize()`
- Возвращает размер в байтах

**`prepare_for_telegram(filepath)`**:
- Если файл > 50 MB — сжимает
- Если после сжатия всё ещё > 50 MB — возвращает с флагом `True` (предупреждение)
- Возвращает `InputFile` (обёртка aiogram для отправки файлов)

**`cleanup_temp_files(filepaths)`**:
- Удаляет список файлов
- Игнорирует ошибки (файл может уже не существовать)

---

### Прочие директории

#### `downloads/`
**Назначение:** временное хранилище:
- Скачанные страницы манги (`page_1.jpg`, `page_2.jpg`, ...)
- Итоговые PDF-файлы
- Сжатые версии изображений (`*_compressed.jpg`)

Файлы **не удаляются автоматически** после отправки в Telegram. Папку нужно чистить вручную или настроить cron.

#### `alembic/`
**Назначение:** инструмент для миграций базы данных SQLAlchemy. В проекте присутствует, но активно не используется (таблицы создаются через `init_db()`).

---

## Как запустить

### Локально (Windows)

```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Настройка .env (создать файл вручную или через PowerShell)
echo BOT_TOKEN=your_token > .env
echo USE_SQLITE=true >> .env

# 3. Запуск
python run_bot.py

# Или через batch-файл:
start_bot.bat
```

### Docker

```bash
docker-compose up -d
```

---

## Проблемы и ограничения

1. **Токен в `.env` открытым текстом** — файл не должен попадать в git.
2. **FlareSolverr на `localhost:8191`** — если не запущен, fallback на `cloudscraper`.
3. **SQLite в продакшене** — при одновременной работе нескольких пользователей возможны блокировки. Рекомендуется PostgreSQL.
4. **MemoryStorage** — состояния теряются при перезапуске. Для продакшена — Redis.
5. **Жёстко закодирован путь `F:/telegram-bot`** — `run_bot.py` не будет работать на Linux/macOS без правки.
6. **Файлы в `downloads/` не удаляются** — диск может переполниться.
7. **Remanga API** — сайт может изменить формат ответа, и парсер перестанет работать.

---

## Автор

[@Whizyatinka](https://github.com/Whizyatinka)
