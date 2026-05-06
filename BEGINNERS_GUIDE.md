# Пошаговый разбор Telegram-бота для новичков

Этот документ объясняет каждый файл построчно, как будто ты никогда не программировал. Мы пойдем от простого к сложному.

---

## Что вообще происходит? Общая картина

Представь себе ресторан:
- **Пользователь** = гость, который пришел поесть
- **Telegram** = дверь ресторана (через нее гость входит)
- **Бот** = официант, который принимает заказ
- **Dispatcher** = менеджер зала, который распределяет заказы по поварам
- **Обработчики (handlers)** = повара разных специальностей (один готовит пиццу, другой суши)
- **База данных** = блокнот, где записано, что любит каждый постоянный клиент
- **Парсер** = курьер, который ездит в магазин за ингредиентами (на сайт remanga.org)

Когда ты пишешь боту "Наруто", происходит так:
1. Telegram передает сообщение боту
2. Dispatcher смотрит: "Ага, это текст, не команда"
3. Отдает повару-обработчику для поиска манги
4. Обработчик просит курьера-парсера найти "Наруто" на remanga.org
5. Парсер возвращает список найденного
6. Обработчик просит сделать красивые кнопки
7. Бот отправляет тебе результат с кнопками

---

## Файл 1: `run_bot.py` — Точка входа (запуск)

Это как кнопка "Старт" на машине. Когда ты нажимаешь ее, машина заводится.

```python
import asyncio

from app.loader import start
```
**Разбор импортов:**
- `asyncio` — позволяет программе делать несколько дел одновременно (это как если бы у тебя было 10 рук)
- `from app.loader import start` — берем из папки `app` файл `loader.py` функцию `start`. Это как достать конкретный инструмент из ящика.

```python
async def main():
    await start()
```
**Что это:**
- `def` — мы создаем функцию (подпрограмму, блок кода с именем)
- `async` — эта функция умеет "засыпать" и просыпаться (асинхронность). Когда она ждет ответа от Telegram, она не блокирует всю программу.
- `await` — "подожди, пока `start()` закончит работу". Это как стоять у микроволновки и ждать, пока еда нагреется.

```python
if __name__ == "__main__":
    asyncio.run(main())
```
**Что это:** Самая известная строка в Python.
- `__name__` — специальная переменная, которая показывает, как запущен файл
- `"__main__"` — это значит "файл запущен напрямую" (а не импортирован как библиотека)
- `asyncio.run(main())` — запускает нашу асинхронную функцию `main()`

**Простыми словами:** "Если этот файл запущен как главный, а не подключен к другому файлу — начни работу".

---

## Файл 2: `app/loader.py` — Заводская бота

Этот файл создает бота, подключает его к Telegram и запускает бесконечный цикл ожидания сообщений.

```python
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
```

**Разбор импортов:**
- `logging` — инструмент для записи логов (сообщений вроде "Вот что происходит"). Это как видеокамера, которая пишет, что делает программа.
- `Bot` — класс из aiogram. Это сам бот, через него мы общаемся с Telegram.
- `Dispatcher` — диспетчер. Он смотрит на каждое входящее сообщение и решает, какой обработчик вызвать.
- `DefaultBotProperties` — настройки по умолчанию для бота.
- `ParseMode.HTML` — говорит боту: "В моих сообщениях может быть HTML-разметка" (жирный текст, курсив, и т.д.).
- `MemoryStorage` — хранилище в оперативной памяти. Бот запоминает, в каком "состоянии" находится каждый пользователь.
- `AiohttpSession` — HTTP-сессия для связи с Telegram.

```python
from app.config import config
from app.models.database import init_db
```
**Что это:** Мы импортируем:
- `config` — объект с настройками (токен бота, пароли и т.д.)
- `init_db` — функцию, которая создает таблицы в базе данных

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```
**Что это:**
- `basicConfig` — настраиваем логирование. `level=logging.INFO` значит "пиши все сообщения уровня INFO и выше" (INFO, WARNING, ERROR).
- `getLogger(__name__)` — создаем логгер с именем текущего файла (`app.loader`). Это как назвать камеру "loader", чтобы знать, откуда запись.

```python
bot: Bot | None = None
dp: Dispatcher | None = None
```
**Что это:** Глобальные переменные. Это как ящик, в котором лежит бот и диспетчер. Сначала они пустые (`None`), потом их наполняют.
- `bot: Bot | None` — переменная, которая может хранить бота или быть пустой
- `dp: Dispatcher | None` — переменная для диспетчера

```python
async def load():
    global bot, dp

    session = AiohttpSession()
```
**Что это:** Функция `load` инициализирует бота. `global bot, dp` — говорим: "мы будем менять глобальные переменные, а не создавать новые локальные".
- `AiohttpSession()` — создаем HTTP-сессию. Сессия — это соединение, которое можно переиспользовать. Это как открыть дверь в Telegram и держать ее открытой, пока общаемся.

```python
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session
    )
```
**Разбор:**
- `bot = Bot(...)` — создаем объект бота и кладем в глобальную переменную
- `token=config.BOT_TOKEN` — берем токен из `.env` файла (через `config`)
- `default=DefaultBotProperties(parse_mode=ParseMode.HTML)` — говорим: "По умолчанию сообщения — HTML"
- `session=session` — используем нашу HTTP-сессию

```python
    dp = Dispatcher(storage=MemoryStorage())
```
**Что это:**
- `MemoryStorage()` — создаем хранилище в оперативной памяти. Оно хранит: "Пользователь 12345 сейчас в состоянии ожидания названия манги".
- `Dispatcher(storage=...)` — создаем диспетчер и отдаем ему наше хранилище.

**Простым языком:** Диспетчер — это секретарь, который принимает все звонки (сообщения) и решает, кому передать трубку. Ему нужно знать "состояние" каждого клиента, поэтому мы даем ему блокнот (`storage`).

```python
        await init_db()
        logger.info("Database initialized")
```
**Что это:**
- `await init_db()` — создаем таблицы в базе данных (если их еще нет)
- `logger.info(...)` — записываем в лог: "База данных инициализирована"

```python
        await cls._load_handlers()
        logger.info("Handlers loaded")
```
**Что это:**
- `_load_handlers()` — приватный метод (начинается с `_`) для загрузки обработчиков
- Загружаются три роутера: `commands`, `manga`, `callbacks`

```python
def _load_handlers():
    from app.handlers import commands, manga, callbacks
    dp.include_router(commands.router)
    dp.include_router(manga.router)
    dp.include_router(callbacks.router)
```
**Разбор:**
- `from app.handlers import ...` — импортируем три файла с обработчиками команд, манги и callback-ов
- Почему импорт внутри функции? Чтобы избежать циклических зависимостей (когда файлы импортируют друг друга).
- `dp.include_router(...)` — подключаем три роутера к диспетчеру.
- `commands.router` — обработчики команд (/start, /help, /stats)
- `manga.router` — обработчики поиска манги
- `callbacks.router` — обработчики нажатий на кнопки

**Аналогия:** Это как секретарю дать три справочника: один для заказов пиццы, другой для суши, третий для жалоб. Когда звонит клиент, секретарь смотрит, что сказал клиент, и открывает нужный справочник.

```python
async def start():
    await load()
    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started!")
    await dp.start_polling(bot)
```
**Разбор пошагово:**
1. `await load()` — сначала инициализируем все (база, обработчики)
2. `delete_webhook(drop_pending_updates=True)` — удаляем webhook и сбрасываем старые сообщения. Если бот был перезапущен, он не обработает сообщения, которые накопились, пока был выключен.
3. `dp.start_polling(bot)` — запускаем бесконечный цикл "опроса" Telegram.

**Простыми словами:** Бот садится на стул и начинает постоянно спрашивать Telegram: "Ну что, есть сообщения? ... А сейчас? ... А сейчас?" Это и есть polling.

```python
async def close():
    await bot.session.close()
    logger.info("Bot closed")
```
**Что это:** Закрываем сессию бота (соединение с Telegram). Это как повесить трубку после разговора.

---

## Файл 3: `app/config.py` — Настройки бота

Этот файл читает секреты и настройки из файла `.env`.

```python
import os
from dataclasses import dataclass
from dotenv import load_dotenv
```
**Разбор:**
- `os` — работа с операционной системой, в том числе `os.getenv()` для чтения переменных окружения
- `dataclass` — декоратор, который автоматически создает конструктор для класса
- `load_dotenv` — функция, которая читает файл `.env` и загружает переменные в окружение

```python
load_dotenv()
```
**Что это:** "Прочитай файл `.env` в текущей папке и сделай его переменные доступными через `os.getenv()`".

**Аналогия:** Это как зайти в комнату и прочитать стикеры на стене. Каждый стикер — переменная (например, `BOT_TOKEN=12345`).

```python
@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
```
**Разбор:**
- `@dataclass` — говорим Python: "Это класс для хранения данных. Создай за меня `__init__`, `__repr__` и другие служебные методы".
- `BOT_TOKEN: str` — поле `BOT_TOKEN` типа строка
- `os.getenv("BOT_TOKEN", "")` — читаем переменную окружения `BOT_TOKEN`. Если ее нет — используем пустую строку `""`.

**Простым языком:** Это как бланк с полями. Мы говорим: "Вот бланк настроек. Поле `BOT_TOKEN` заполни из переменной окружения или оставь пустым".

```python
    PROXY_URL: str = os.getenv("PROXY_URL", "")
```
**Что это:** Если нужен прокси-сервер для подключения к Telegram. Сейчас не используется (пустая строка).

```python
    MAX_FILE_SIZE_TG: int = 50 * 1024 * 1024
```
**Что это:** Константа. `50 * 1024 * 1024` = 50 мегабайт в байтах. Telegram не принимает файлы больше 50 МБ через обычные методы.

```python
    COMPRESSION_QUALITY: int = 85
    MAX_IMAGE_DIMENSION: int = 2000
```
**Что это:**
- `COMPRESSION_QUALITY=85` — качество JPEG при сжатии (0-100). 85 — хороший баланс между качеством и размером.
- `MAX_IMAGE_DIMENSION=2000` — максимальный размер стороны картинки в пикселях.

```python
config = Config()
```
**Что это:** Создаем ОДИН объект настроек. Этот объект (`config`) импортируется во все файлы проекта. Это паттерн **Singleton** (Одиночка) — гарантия, что настройки созданы один раз и везде используются одинаковые.

---

## Файл 4: `app/models/database.py` — База данных

Этот файл описывает, какие таблицы есть в базе данных и как с ними работать.

**Что такое база данных?** Это как Excel-таблица, которая живет в файле. Мы можем записывать туда данные, читать их, изменять и удалять.

```python
from contextlib import asynccontextmanager
from datetime import datetime
```
**Разбор:**
- `contextlib.asynccontextmanager` — декоратор, который превращает функцию в асинхронный контекстный менеджер (`async with`).
- `datetime` — работа с датами и временем (чтобы записывать "когда пользователь зарегистрировался")

```python
from sqlalchemy import String, Integer, ForeignKey, DateTime, BigInteger, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
```

**SQLAlchemy** — это ORM (Object-Relational Mapping). Это переводчик между миром Python-объектов и миром SQL-таблиц.

**Разбор импортов:**
- `String`, `Integer`, `DateTime` — типы данных для колонок таблицы
- `ForeignKey` — связь между таблицами (как связь между листами Excel через формулу ВПР)
- `DeclarativeBase` — базовый класс для всех моделей
- `Mapped`, `mapped_column` — новый стиль SQLAlchemy 2.0 для описания колонок
- `relationship` — связь между таблицами на уровне Python-объектов
- `AsyncSession`, `async_sessionmaker`, `create_async_engine` — асинхронные инструменты для работы с БД

```python
class Base(DeclarativeBase):
    pass
```
**Что это:** Создаем базовый класс для всех наших таблиц. Все модели будут наследоваться от него. Это как общая бумага для всех анкет.

```python
DATABASE_URL = "sqlite+aiosqlite:///telegram_bot.db"

async_engine = create_async_engine(DATABASE_URL, echo=False)
```
**Разбор:**
- `DATABASE_URL` — строка подключения к SQLite. Файл `telegram_bot.db` создается в текущей папке.
- `create_async_engine` — создаем "движок" БД (точка входа для всех операций)
- `echo=False` — не показывать SQL-запросы в консоли

**Почему SQLite?** Для бота-читалки нагрузка минимальная (пользователи, статистика, callback-кеш). SQLite — это файл, не требует отдельного сервера. Просто, быстро, не нужен Docker с PostgreSQL.

```python
async_session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
```
**Разбор:**
- `async_sessionmaker` — фабрика сессий. Каждый раз, когда мы хотим поработать с БД, фабрика выдает нам новую сессию.
- `class_=AsyncSession` — тип сессии
- `expire_on_commit=False` — после сохранения данных объект не "протухает" (можно и дальше с ним работать)

**Аналогия:** Сессия — это как чековая книжка. Ты делаешь записи (добавляешь данные), и только когда говоришь "commit" — чек уходит в банк (данные записываются в БД).

---

### Таблица `User`

```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    stats: Mapped["UserStats"] = relationship("UserStats", back_populates="user", uselist=False)
```

**Разбор построчно:**

`class User(Base):` — создаем модель "Пользователь", наследуемся от `Base`.

`__tablename__ = "users"` — имя таблицы в БД будет `users`.

`id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)`
- `id` — имя колонки
- `Mapped[int]` — тип: целое число
- `primary_key=True` — это главный идентификатор записи (как номер паспорта)
- `autoincrement=True` — SQL сам назначает номер: 1, 2, 3...

`tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)`
- `BigInteger` — большое целое (Telegram ID могут быть очень большими числами)
- `unique=True` — не может быть двух пользователей с одинаковым `tg_id`
- `nullable=False` — обязательное поле, нельзя оставить пустым

`username: Mapped[str] = mapped_column(String(255), nullable=True)`
- `String(255)` — строка максимум 255 символов
- `nullable=True` — может быть пустым (не у всех есть @username в Telegram)

`created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)`
- `DateTime` — тип дата/время
- `default=datetime.utcnow` — если не указано, ставить текущее время UTC

`stats: Mapped["UserStats"] = relationship(...)`
- Это не колонка! Это Python-ссылка на связанный объект.
- `"UserStats"` — имя связанной модели (в кавычках, потому что она объявлена ниже)
- `back_populates="user"` — обратная связь: из `UserStats` можно попасть в `User`
- `uselist=False` — связь "один к одному" (у одного пользователя — одна статистика)

---

### Таблица `UserStats`

```python
class UserStats(Base):
    __tablename__ = "user_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"), unique=True)
    manga_chapters_count: Mapped[int] = mapped_column(Integer, default=0)
    user: Mapped["User"] = relationship("User", back_populates="stats")
```

**Ключевое:** `ForeignKey("users.tg_id")` — это связь с таблицей `users`, колонка `tg_id`. Это как написать в анкете: "Мой номер паспорта — такой же, как у человека в таблице users".

**Связь "один к одному":**
- Один `User` → один `UserStats`
- Через `user.stats` можно получить статистику
- Через `stats.user` можно получить пользователя

---

### Таблица `CallbackData`

```python
class CallbackData(Base):
    __tablename__ = "callback_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    short_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    data_type: Mapped[str] = mapped_column(String(32), nullable=False)
    full_data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Зачем нужна:** Помнишь, что callback-кнопки в Telegram ограничены 64 байтами? Эта таблица хранит соответствие: короткий ID → полные данные.

- `short_id` — 16-символьный MD5-hash, который передается в кнопке
- `full_data` — полные данные в формате JSON (например, `{"manga_id": "naruto", "chapter_id": "12345"}`)
- `index=True` — создаем индекс для быстрого поиска

**Индекс** — это как указатель в книге. Без индекса БД перебирает все записи подряд. С индексом — сразу находит нужную.

---

### Таблица `DownloadedChapter`

```python
class DownloadedChapter(Base):
    __tablename__ = "downloaded_chapters"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    manga_id: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter_id: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter_number: Mapped[float] = mapped_column(nullable=False)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Зачем нужна:** Запоминает, какие главы уже скачал пользователь. Чтобы не скачивать дважды.

- `user_id + manga_id + chapter_id` — комбинация, которая должна быть уникальной (хотя тут нет явного `unique=True`)
- `chapter_number` — `float`, потому что главы могут быть 1.5, 2.5 и т.д.

---

### Функция `get_db()`

```python
@asynccontextmanager
async def get_db():
    async with async_session_factory() as session:
        yield session
```

**Разбор:**
- `@asynccontextmanager` — декоратор. Теперь `get_db()` можно использовать как `async with get_db() as db:`.
- `yield session` — отдает сессию внутрь `async with` блока
- При выходе из `async with` сессия автоматически закрывается (даже если была ошибка!)

**Как используется:**
```python
async with get_db() as db:
    # тут работаем с db
    # при выходе из блока сессия закроется сама
```

**Почему так лучше?** Раньше было `async for db in get_db(): ... break` — это был генератор, и приходилось вручную писать `break`. `async with` — естественный способ Python работать с ресурсами, которые нужно закрывать.

---

### Функция `init_db()`

```python
async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

**Разбор:**
- `async_engine.begin()` — начинаем транзакцию с движком БД
- `conn.run_sync(Base.metadata.create_all)` — вызываем синхронную функцию `create_all` внутри асинхронного окружения. Она создает все таблицы, если их нет.

**Простым языком:** "Посмотри на все наши модели (`User`, `UserStats`, `CallbackData`, `DownloadedChapter`) и создай для каждой таблицу в БД, если еще не создана".

---

## Файл 5: `app/handlers/commands.py` — Команды бота

Этот файл обрабатывает текстовые команды: `/start`, `/help`, `/stats`.

```python
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
```

**Разбор:**
- `Router` — роутер (маршрутизатор). Группирует обработчики по темам.
- `Command` — фильтр: "Обрабатывай только сообщения, которые начинаются с /"
- `Message` — тип объекта "Сообщение от пользователя"
- `FSMContext` — контекст конечного автомата (Finite State Machine). Запоминает, в каком состоянии пользователь.
- `State`, `StatesGroup` — классы для создания состояний

**Что такое FSM (Finite State Machine)?**
Представь автомат по продаже кофе:
- Состояние 1: Ждем выбор напитка
- Состояние 2: Ждем деньги
- Состояние 3: Готовим кофе
- Состояние 4: Выдаем кофе

У пользователя бота тоже есть состояния:
- Обычное состояние (ничего не ждем)
- `waiting_for_manga_query` (ждем, когда он напишет название манги)

```python
from app.keyboards.inline import get_main_menu_keyboard
```
**Что это:** Импортируем функцию, которая создает главное меню (кнопки).

```python
logger = logging.getLogger(__name__)
```
**Что это:** Получаем логгер для этого файла. Если в `loader.py` была камера "loader", то тут — камера "commands".

```python
router = Router()
```
**Что это:** Создаем новый роутер. Все обработчики ниже будут зарегистрированы в этом роутере. Потом `loader.py` подключит этот роутер к диспетчеру.

---

### Состояния

```python
class UserStates(StatesGroup):
    waiting_for_manga_query = State()
```

**Разбор:**
- `UserStates` — группа состояний для пользователя
- `waiting_for_manga_query = State()` — состояние "ждем ввода названия манги"

**Как это работает:**
1. Пользователь нажимает "🔍 Поиск манги"
2. Бот ставит ему состояние `waiting_for_manga_query`
3. Бот ждет СЛЕДУЮЩЕГО сообщения от этого пользователя
4. Когда сообщение приходит, диспетчер видит: "Ага, этот пользователь в состоянии waiting_for_manga_query! Значит, это название манги!"
5. Обрабатывает через `manga_search_handler()`

---

### Обработчик /start

```python
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я бот для поиска и скачивания манги.\n\n"
        "Выберите режим из меню ниже:",
        reply_markup=get_main_menu_keyboard()
    )
```

**Разбор построчно:**

`@router.message(Command("start"))` — декоратор. Это как стикер на двери: "Если кто-то скажет /start — вызывай эту функцию".

`async def cmd_start(message: Message, state: FSMContext):` — определяем функцию с двумя параметрами:
- `message` — объект сообщения (текст, кто написал, когда и т.д.)
- `state` — объект состояния этого пользователя

`await state.clear()` — "Сбрось все состояния пользователя". Если он был в процессе поиска, прервем его и начнем сначала.

`await message.answer(...)` — отправить ответ пользователю.

`reply_markup=get_main_menu_keyboard()` — прикрепить к сообщению клавиатуру (кнопки).

---

### Обработчик /help

```python
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Инструкция по использованию:</b>\n\n"
        "1. <b>Поиск манги</b> - найдите мангу...\n"
        "2. <b>Статистика</b> - посмотрите сколько глав...\n\n"
        "⏱️ Файлы манги конвертируются в PDF..."
    )
```

**Разбор:**
- `<b>...</b>` — HTML-теги жирного текста (работают потому что в `loader.py` мы установили `parse_mode=ParseMode.HTML`)
- `\n\n` — двойной перевод строки (пустая строка между абзацами)

---

### Обработчик /stats

```python
from sqlalchemy import select
from app.models.database import User, UserStats, get_db
```
**Что это:** Импорты SQLAlchemy и моделей БД — теперь наверху файла, как и положено.

```python
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    tg_id = message.from_user.id
```

**Разбор:**
- `message.from_user.id` — Telegram ID пользователя, который отправил сообщение

```python
    async with get_db() as db:
        result = await db.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
```

**Разбор:**
- `async with get_db() as db` — получаем сессию БД (и автоматически закроем при выходе)
- `select(User)` — SQL-запрос: "Выбери все колонки из таблицы users"
- `.where(User.tg_id == tg_id)` — условие: "где tg_id равен ID пользователя"
- `await db.execute(...)` — выполнить запрос
- `result.scalar_one_or_none()` — взять ОДНУ запись или `None`, если ничего не найдено

**Почему `scalar_one_or_none()` а не просто `one()`?** Потому что если пользователь еще не зарегистрирован, `one()` упадет с ошибкой. А `scalar_one_or_none()` безопасно вернет `None`.

```python
        if not user:
            await message.answer("Вы еще ничего не скачивали. Начните поиск!")
            return
```
**Что это:** Если пользователя нет в БД — отправляем сообщение и выходим (`return`).

```python
        stats = user.stats
        if not stats:
            stats = UserStats(user_id=tg_id, manga_chapters_count=0)
```
**Что это:**
- `user.stats` — благодаря `relationship` SQLAlchemy автоматически подгружает связанную статистику
- Если статистики нет — создаем пустую (0 глав)

```python
        await message.answer(
            f"📊 <b>Ваша статистика:</b>\n\n"
            f"📚 <b>Манга:</b> {stats.manga_chapters_count} глав"
        )
```
**Что это:**
- `f"..."` — f-string, форматированная строка. Внутри `{stats.manga_chapters_count}` подставляется значение.

---

## Файл 6: `app/handlers/manga.py` — Поиск манги

Этот файл обрабатывает сценарий поиска манги.

```python
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bs4 import BeautifulSoup

from app.handlers.commands import UserStates
from app.models.database import get_db
from app.keyboards.inline import get_manga_card_keyboard, get_search_keyboard
from app.services.manga_service import MangaService
```

**Разбор новых импортов:**
- `F` — фильтр-объект из aiogram. `F.text == "🔍 Поиск манги"` означает "триггерись только если текст сообщения равен этому".
- `CallbackQuery` — объект нажатия на inline-кнопку
- `BeautifulSoup` — библиотека для очистки HTML из текста описания манги
- `UserStates` — наши состояния из `commands.py`
- `MangaService` — сервис для работы с мангой (поиск, скачивание)

---

### Начало поиска

```python
@router.message(F.text == "🔍 Поиск манги")
async def manga_search_start(message: Message, state: FSMContext):
    logger.info(f"Text search triggered by user {message.from_user.id}")
    await state.set_state(UserStates.waiting_for_manga_query)
    await message.answer("Введите название манги для поиска:")
```

**Разбор:**
- `F.text == "🔍 Поиск манги"` — фильтр. Сработает, если пользователь нажал кнопку "🔍 Поиск манги" (или ввел точно этот текст).
- `logger.info(...)` — пишем в лог: "Пользователь N начал поиск"
- `await state.set_state(...)` — переводим пользователя в состояние ожидания названия
- `await message.answer(...)` — просим ввести название

**Простым языком:** "Официант подходит к столику и спрашивает: "Что будете заказывать?" Записывает в блокнот: "Столик №5 — жду заказ".

---

### Обработка введенного названия

```python
@router.message(UserStates.waiting_for_manga_query)
async def manga_search_handler(message: Message, state: FSMContext):
    logger.info(f"Search handler triggered with query: {message.text}")
    query = message.text.strip()
    if not query:
        await message.answer("Введите название для поиска")
        return
```

**Разбор:**
- `@router.message(UserStates.waiting_for_manga_query)` — сработает ТОЛЬКО если пользователь в состоянии `waiting_for_manga_query`
- `message.text.strip()` — берем текст сообщения и убираем пробелы по краям ("  Наруто  " → "Наруто")
- `if not query:` — если строка пустая после удаления пробелов
- `return` — выходим из функции (ничего больше не делаем)

```python
    await state.clear()
```
**Что это:** Сбрасываем состояние. Пользователь больше не "в процессе поиска". Это важно, потому что следующее его сообщение не должно восприниматься как название манги.

```python
    async with get_db() as db:
        service = MangaService(db)
```
**Что это:**
- Получаем сессию БД
- Создаем объект `MangaService`, передавая ему сессию БД. Теперь сервис может и искать мангу, и записывать в БД.

```python
        try:
            logger.info(f"Starting search for: {query}")
            results = await service.search(query)
            logger.info(f"Search returned {len(results)} results")
```
**Разбор:**
- `try:` — начинаем блок "попытка". Если внутри случится ошибка, программа не упадет, а перейдет к `except`.
- `await service.search(query)` — вызываем поиск. Это может занять время (сетевой запрос), поэтому `await`.
- `len(results)` — количество найденных результатов

```python
            if not results:
                await message.answer("Манга не найдена. Попробуйте другой запрос.")
                return
```
**Что это:** Если список пустой — скажем пользователю и выйдем.

```python
            results_data = [
                {"id": str(idx), "title": r.title, "cover_url": r.cover_url, "real_id": r.id}
                for idx, r in enumerate(results)
            ]
```

**Разбор:**
- Это **list comprehension** (генератор списка). Создаем новый список на основе `results`.
- `enumerate(results)` — нумерует результаты: (0, result1), (1, result2), ...
- `idx` — индекс (0, 1, 2...)
- `r` — объект `MangaTitleInfo`
- `str(idx)` — превращаем число в строку
- `"real_id": r.id` — сохраняем реальный ID (dir из Remanga)

**Зачем это:** Клавиатуре нужны простые ID ("0", "1", "2"), а не длинные slug. Мы создаем отображение индекс → реальный ID.

```python
            await state.update_data(manga_mapping={str(idx): r.id for idx, r in enumerate(results)})
```
**Что это:** Сохраняем в FSM-state словарь: `{"0": "naruto", "1": "bleach", ...}`. Это нужно, потому что когда пользователь нажмет кнопку с результатом, придет callback вида `manga_card:0`, и мы по этому словарю найдем реальный ID.

```python
            await message.answer(
                f"🔍 Результаты поиска по '{query}':",
                reply_markup=get_search_keyboard(results_data)
            )
```
**Что это:** Отправляем сообщение с результатами и inline-кнопками. Каждая кнопка — название манги.

```python
        except Exception as e:
            logger.error(f"Error in search handler: {e}", exc_info=True)
            await message.answer("Произошла ошибка при поиске. Попробуйте позже.")
        finally:
            await service.close()
```

**Разбор:**
- `except Exception as e:` — если в `try` случилась ЛЮБАЯ ошибка, ловим ее здесь
- `logger.error(..., exc_info=True)` — записываем ошибку в лог вместе с полной информацией (traceback)
- `await message.answer("Произошла ошибка...")` — говорим пользователю, что что-то пошло не так
- `finally:` — этот блок ВСЕГДА выполняется, даже если была ошибка
- `await service.close()` — закрываем HTTP-сессию парсера (чтобы не оставлять открытые соединения)

---

### Обработка нажатия на результат

```python
@router.callback_query(F.data.startswith("manga_card:"))
async def manga_card_callback(callback: CallbackQuery, state: FSMContext):
    idx = callback.data.split(":")[1]
```

**Разбор:**
- `@router.callback_query(...)` — обрабатываем нажатие inline-кнопки
- `F.data.startswith("manga_card:")` — только если callback_data начинается с "manga_card:"
- `callback.data` — строка вида "manga_card:0"
- `.split(":")` — разбиваем по двоеточию: `["manga_card", "0"]`
- `[1]` — берем второй элемент: "0"

```python
    data = await state.get_data()
    manga_mapping = data.get("manga_mapping", {})
    manga_id = manga_mapping.get(idx)
```
**Разбор:**
- `await state.get_data()` — достаем все данные, которые мы сохранили в state
- `data.get("manga_mapping", {})` — берем словарь маппинга. Если его нет — пустой словарь `{}`.
- `manga_mapping.get(idx)` — ищем реальный ID по индексу "0", "1" и т.д.

```python
    if not manga_id:
        await callback.answer("Манга не найдена")
        return
```
**Что это:** Если по какой-то причине ID не нашелся (например, state протух) — скажем об этом и выйдем.

```python
    async with get_db() as db:
        service = MangaService(db)
        try:
            manga = await service.get_title_details(manga_id)
```
**Что это:** Получаем ПОЛНУЮ информацию о манге (описание, год, статус, обложку).

```python
            cover_text = f"📖 <b>{manga.title}</b>\n\n"
            
            if manga.description:
                desc = BeautifulSoup(manga.description, "html.parser").get_text()
                desc = desc[:300] + "..." if len(desc) > 300 else desc
                cover_text += f"<i>{desc}</i>\n\n"
```

**Разбор:**
- Формируем текст карточки
- `BeautifulSoup(manga.description, "html.parser")` — парсим HTML-описание
- `.get_text()` — извлекаем только текст, без HTML-тегов
- `desc[:300] + "..."` — обрезаем до 300 символов и добавляем многоточие
- `<i>...</i>` — курсив в HTML

```python
            if manga.year:
                cover_text += f"📅 Год: {manga.year}\n"
            if manga.status:
                cover_text += f"📌 Статус: {manga.status}\n"
            if manga.chapters_count:
                cover_text += f"📚 Глав: {manga.chapters_count}\n"
```
**Что это:** Дополняем текст только теми полями, которые есть. Если статуса нет — не пишем "Статус: None".

```python
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
```

**Разбор:**
- `answer_photo(...)` — отправляем фото с подписью (caption)
- `photo=manga.cover_url` — Telegram сам скачает картинку по URL и покажет
- `reply_markup=get_manga_card_keyboard(manga_id)` — кнопки: "Скачать всё", "По главам", "По томам", "Назад"
- `try/except` — если не удалось отправить фото (например, URL битый), отправляем просто текст

---

## Файл 7: `app/handlers/callbacks.py` — Обработка кнопок

Это самый большой файл. Он обрабатывает ВСЕ нажатия inline-кнопок.

### Кнопка "По главам"

```python
@router.callback_query(F.data.startswith("manga_by_chapter:"))
async def manga_chapters_callback(callback: CallbackQuery, state: FSMContext):
    manga_id = callback.data.split(":")[1]
```
**Разбор:**
- Callback вида: `manga_by_chapter:naruto`
- `split(":")[1]` → "naruto"

```python
    async with get_db() as db:
        service = MangaService(db)
        try:
            chapters = await service.get_chapters(manga_id)
            if not chapters:
                await callback.answer("Главы не найдены")
                return
```
**Что это:** Получаем список глав. Если пусто — скажем и выйдем.

```python
            chapters = sorted(chapters, key=lambda x: x.number)
```
**Разбор:**
- `sorted(...)` — сортируем список
- `key=lambda x: x.number` — правило сортировки: "по полю number"
- `lambda` — анонимная функция. `lambda x: x.number` значит "для объекта x верни x.number"

**Аналогия:** Это как отсортировать книги на полке по номерам от 1 до 100.

```python
            chapters_data = [
                {"id": ch.id, "number": ch.number, "name": ch.name}
                for ch in chapters
            ]
```
**Что это:** Превращаем объекты `ChapterInfo` в простые словари. Это нужно для клавиатуры.

```python
            keyboard = await get_manga_chapters_keyboard(
                chapters_data, manga_id, callback.from_user.id, db
            )
```
**Что это:** Просим создать клавиатуру со списком глав. `await` потому что функция асинхронная (создает callback_id в БД).

```python
            await callback.message.answer(
                f"📄 Выберите главу ({len(chapters)} глав всего):",
                reply_markup=keyboard
            )
        finally:
            await service.close()

    await callback.answer()
```
**Разбор:**
- `callback.message.answer(...)` — отправляем новое сообщение с клавиатурой
- `await callback.answer()` — ОБЯЗАТЕЛЬНО отвечаем на callback. Если не ответить, у пользователя будет "крутящийся кружок" на кнопке.

---

### Постраничная навигация по главам

```python
@router.callback_query(F.data.startswith("manga_chapters:"))
async def manga_chapters_page_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    manga_id = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0
```

**Разбор:**
- Callback вида: `manga_chapters:naruto:1` (вторая страница)
- `split(":")` → `["manga_chapters", "naruto", "1"]`
- `page = int(parts[2])` → 1
- `if len(parts) > 2 else 0` — если номер страницы не указан, считаем, что это 0

```python
            keyboard = await get_manga_chapters_keyboard(
                chapters_data, manga_id, callback.from_user.id, db, page
            )
            
            await callback.message.edit_text(
                f"📄 Выберите главу ({len(chapters_data)} глав всего):",
                reply_markup=keyboard
            )
```
**Разбор:**
- `edit_text(...)` — меняем текст СУЩЕСТВУЮЩЕГО сообщения (вместо отправки нового)
- `reply_markup=keyboard` — меняем клавиатуру

**Аналогия:** Это как исправить запись в блокноте, а не писать новую.

---

### Кнопка "По томам"

```python
@router.callback_query(F.data.startswith("manga_by_volume:"))
async def manga_volumes_callback(callback: CallbackQuery, state: FSMContext):
    manga_id = callback.data.split(":")[1]
    
    async with get_db() as db:
        service = MangaService(db)
        try:
            chapters = await service.get_chapters(manga_id)
```

```python
            volumes_dict = {}
            for ch in chapters:
                if ch.volume:
                    if ch.volume not in volumes_dict:
                        volumes_dict[ch.volume] = []
                    volumes_dict[ch.volume].append(ch)
```

**Разбор:**
- Создаем пустой словарь `volumes_dict`
- Для каждой главы смотрим: есть ли у нее номер тома (`ch.volume`)?
- Если тома еще нет в словаре — создаем для него пустой список
- Добавляем главу в список своего тома

**Результат:**
```python
{
    1: [Глава1, Глава2, Глава3],  # Том 1
    2: [Глава4, Глава5],           # Том 2
    3: [Глава6]                     # Том 3
}
```

```python
            await state.update_data(
                volumes_dict=volumes_dict,
                current_manga_id=manga_id
            )
```
**Что это:** Сохраняем `volumes_dict` в FSM-state! Это важно, потому что когда пользователь выберет том, нам нужно будет получить список глав этого тома. Мы не хотим заново запрашивать API Remanga.

```python
            text = f"📚 Выберите том ({len(chapters)} глав всего):\n\n"
            for vol_num in sorted(volumes_dict.keys()):
                text += f"📖 Том {vol_num}: {len(volumes_dict[vol_num])} глав\n"
```
**Что это:** Формируем красивый текст со списком томов.

---

### Выбор конкретного тома

```python
@router.callback_query(F.data.startswith("vol:"))
async def manga_volume_chapters_callback(callback: CallbackQuery, state: FSMContext):
    short_id = callback.data.split(":")[1]
```
**Разбор:** Callback вида `vol:abc123def456`. `short_id` — это MD5-hash, который мы создали через `CallbackManager`.

```python
    async with get_db() as db:
        data = await CallbackManager.get_callback_data(db, short_id, callback.from_user.id)
        if not data:
            await callback.answer("Данные не найдены")
            return
```
**Разбор:**
- Идем в таблицу `callback_data` БД
- Ищем запись с `short_id=abc123...` и `user_id=текущий пользователь`
- Если не нашли — значит callback протух или подделан

```python
        manga_id = data.get("manga_id")
        volume_num = data.get("volume_num")
```
**Что это:** Достаем реальные данные из JSON. Например: `{"manga_id": "naruto", "volume_num": 1}`.

```python
        state_data = await state.get_data()
        volumes_dict = state_data.get("volumes_dict", {})
```
**Что это:** Достаем `volumes_dict`, который мы сохранили раньше. В нем лежат все главы, сгруппированные по томам.

```python
        volume_chapters = sorted(volumes_dict[volume_num], key=lambda x: x.number)
```
**Что это:** Берем главы конкретного тома и сортируем по номеру.

---

### Скачивание главы (самый важный обработчик)

```python
@router.callback_query(F.data.startswith("ch:"))
async def manga_chapter_download_callback(callback: CallbackQuery, state: FSMContext):
    short_id = callback.data.split(":")[1]
```

```python
    async with get_db() as db:
        data = await CallbackManager.get_callback_data(db, short_id, callback.from_user.id)
        manga_id = data.get("manga_id")
        chapter_id = data.get("chapter_id")
        chapter_num = data.get("number")
```
**Разбор:** Получаем данные о главе из таблицы `callback_data`.

```python
        service = MangaService(db)
        try:
            manga = await service.get_title_details(manga_id)
            if not manga:
                await callback.message.answer("Манга не найдена")
                return
```
**Что это:** Получаем информацию о манге (нужно название для имени файла).

```python
            already_downloaded = await service.is_chapter_downloaded(
                callback.from_user.id, manga_id, chapter_id
            )
            
            if already_downloaded:
                await callback.message.answer(f"✅ Глава {chapter_num} уже была скачана ранее")
                await callback.answer()
                return
```
**Разбор:**
- Проверяем таблицу `downloaded_chapters`
- Если уже скачана — сообщаем и выходим
- Экономим трафик и время

```python
            progress_msg = await callback.message.answer(
                f"⏳ Скачиваю главу {chapter_num}...\n\n▱▱▱▱▱▱▱▱▱▱ 0%"
            )
```
**Что это:** Отправляем сообщение с прогресс-баром. `progress_msg` — объект сообщения, который мы потом сможем редактировать.

```python
            async def update_progress(current: int, total: int, status: str):
                try:
                    if status == "downloading":
                        percent = int((current / total) * 100)
                        filled = int((current / total) * 10)
                        bar = "▰" * filled + "▱" * (10 - filled)
                        text = f"⏳ Скачиваю главу {chapter_num}...\n\n{bar} {percent}%\nСтраница {current}/{total}"
                        await progress_msg.edit_text(text)
                    elif status == "creating_pdf":
                        await progress_msg.edit_text(f"📄 Создаю PDF для главы {chapter_num}...")
                except Exception as e:
                    logger.error(f"Failed to update progress: {e}")
```

**Разбор:**
- Мы определяем функцию ВНУТРИ другой функции. Это называется **вложенная функция**.
- `current` — сколько страниц скачано
- `total` — всего страниц
- `filled = int((current / total) * 10)` — сколько квадратиков ▰ заполнить (от 0 до 10)
- `"▰" * filled` — повторяем символ `filled` раз (например, "▰▰▰")
- `"▱" * (10 - filled)` — оставшиеся пустые квадратики
- `progress_msg.edit_text(...)` — меняем текст сообщения

**Пример прогресса:**
```
⏳ Скачиваю главу 15...

▰▰▰▱▱▱▱▱▱▱ 30%
Страница 6/20
```

```python
            filepath, is_cached = await service.download_chapter(
                chapter_id, manga_id, manga.title, chapter_num, callback.from_user.id,
                progress_callback=update_progress
            )
```
**Разбор:**
- Вызываем скачивание главы
- Передаем `progress_callback=update_progress` — нашу функцию прогресса
- Возвращает: путь к PDF и флаг "уже скачана" (но мы это проверили раньше)

```python
            if filepath:
                try:
                    await progress_msg.delete()
                except:
                    pass
```
**Что это:** Удаляем сообщение с прогрессом. Если не получилось удалить (например, сообщение уже старое) — игнорируем ошибку (`pass`).

```python
                file_size = os.path.getsize(filepath)
                file_size_mb = file_size / (1024 * 1024)
```
**Разбор:**
- `os.path.getsize()` — узнать размер файла в байтах (`os` импортирован наверху файла)
- Делим на `1024 * 1024` = 1 048 576, чтобы получить мегабайты

```python
                if file_size > 50 * 1024 * 1024:
                    await callback.message.answer(
                        f"⚠️ Файл слишком большой ({file_size_mb:.1f} МБ). ..."
                    )
                else:
                    document = FSInputFile(filepath)
                    await callback.message.answer_document(
                        document,
                        caption=f"📄 {manga.title} - Глава {chapter_num} ({file_size_mb:.1f} МБ)"
                    )
                    await service.update_user_stats(callback.from_user.id, 1)
```

**Разбор:**
- `FSInputFile(filepath)` — обертка aiogram для отправки файла с диска
- `answer_document(...)` — отправляем как документ (PDF)
- `caption` — подпись к файлу
- `update_user_stats(..., 1)` — увеличиваем счетчик скачанных глав на 1

---

### Скачивание всего тома

```python
@router.callback_query(F.data.startswith("vdl:"))
async def manga_volume_download_callback(callback: CallbackQuery, state: FSMContext):
```

Этот обработчик похож на предыдущий, но скачивает ВСЕ главы тома по очереди:

```python
            for ch in chapters:
                try:
                    filepath, _ = await service.download_chapter(...)
                    document = FSInputFile(filepath)
                    await callback.message.answer_document(document, caption=...)
                    downloaded += 1
                except Exception as e:
                    logger.error(f"Error downloading chapter {ch.get('id')}: {e}")
```

**Разбор:**
- Цикл `for ch in chapters` — по каждой главе
- `try/except` внутри цикла — если одна глава не скачалась, переходим к следующей (не ломаем весь процесс)

---

### Скачивание всех глав манги

```python
@router.callback_query(F.data.startswith("manga_download_all:"))
async def manga_download_all_callback(callback: CallbackQuery):
```

```python
            paths = await service.download_all_chapters(manga_id, manga.title, callback.from_user.id)
```
**Что это:** Вызываем метод, который скачивает ВСЕ главы с ограничением concurrency (3 параллельных загрузки).

---

## Файл 8: `app/keyboards/inline.py` — Клавиатуры

Этот файл создает кнопки. Telegram имеет два типа кнопок:
1. **Reply-кнопки** — кнопки под полем ввода
2. **Inline-кнопки** — кнопки ПОД сообщением (наш случай)

```python
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
```

**Разбор:**
- `InlineKeyboardBuilder` — конструктор клавиатур. Как LEGO — собираем кнопки по кусочкам.
- `InlineKeyboardButton` — одна кнопка
- `InlineKeyboardMarkup` — готовая клавиатура

### Главное меню

```python
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔍 Поиск манги", callback_data="manga_search")
    builder.button(text="📊 Статистика", callback_data="stats")
    builder.button(text="❓ Помощь", callback_data="help")
    
    builder.adjust(1)
    return builder.as_markup()
```

**Разбор:**
- `def ...() -> InlineKeyboardMarkup` — функция возвращает объект типа `InlineKeyboardMarkup`
- `builder = InlineKeyboardBuilder()` — создаем конструктор
- `builder.button(...)` — добавляем кнопку
  - `text` — текст на кнопке
  - `callback_data` — данные, которые придут в бот, когда пользователь нажмет кнопку
- `builder.adjust(1)` — "Располагай по 1 кнопке в ряд". Будет 3 ряда по 1 кнопке.
- `builder.as_markup()` — собрать готовую клавиатуру

**Как это выглядит:**
```
[🔍 Поиск манги]
[📊 Статистика]
[❓ Помощь]
```

### Клавиатура карточки манги

```python
def get_manga_card_keyboard(manga_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📥 Скачать всё", callback_data=f"manga_download_all:{manga_id}")
    builder.button(text="📖 По главам", callback_data=f"manga_by_chapter:{manga_id}")
    builder.button(text="📚 По томам", callback_data=f"manga_by_volume:{manga_id}")
    builder.button(text="🔙 Назад", callback_data="manga_search")
    
    builder.adjust(1)
    return builder.as_markup()
```

**Разбор:**
- `f"manga_download_all:{manga_id}"` — f-string. Подставляем `manga_id` в строку. Получается: `manga_download_all:naruto`.
- Кнопка "Назад" не передает `manga_id` — она просто запускает новый поиск.

### Клавиатура списка глав

```python
async def get_manga_chapters_keyboard(chapters: list, manga_id: str, user_id: int, db, page: int = 0, per_page: int = 20) -> InlineKeyboardMarkup:
```

**Разбор параметров:**
- `chapters` — список глав
- `manga_id` — ID манги
- `user_id` — Telegram ID пользователя (нужен для CallbackManager)
- `db` — сессия БД (нужна для CallbackManager)
- `page` — номер страницы (по умолчанию 0)
- `per_page` — глав на странице (по умолчанию 20)

```python
    start = page * per_page
    end = start + per_page
    page_chapters = chapters[start:end]
```

**Разбор:**
- Если `page=0`: `start=0`, `end=20` — главы с 0 по 19
- Если `page=1`: `start=20`, `end=40` — главы с 20 по 39
- `chapters[start:end]` — **срез** списка

```python
    for ch in page_chapters:
        ch_num = ch.get("number", "?")
        ch_name = ch.get("name", "")
        display_name = f"Глава {ch_num}" + (f" - {ch_name[:20]}" if ch_name else "")
```
**Разбор:**
- `ch.get("number", "?")` — берем номер главы. Если нет — ставим "?"
- `ch_name[:20]` — обрезаем название до 20 символов (чтобы кнопка не была слишком длинной)
- `+ (f" - {ch_name[:20]}" if ch_name else "")` — добавляем название, только если оно есть

```python
        short_id = await CallbackManager.create_callback(
            db, user_id, "chapter",
            {"manga_id": manga_id, "chapter_id": ch.get("id"), "number": ch_num, "name": ch_name}
        )
        
        builder.button(text=display_name, callback_data=f"ch:{short_id}")
```

**Разбор:**
- Создаем в БД запись callback_data с полными данными
- Получаем `short_id` (16 символов)
- Кнопка при нажатии отправит `ch:abc123def456` — укладывается в 64 байта!

```python
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"manga_chapters:{manga_id}:{page-1}"))
    if end < len(chapters):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"manga_chapters:{manga_id}:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
```

**Разбор:**
- `if page > 0` — если не на первой странице — показываем "Назад"
- `if end < len(chapters)` — если есть еще главы — показываем "Вперёд"
- `builder.row(*nav_buttons)` — добавляем ряд с навигационными кнопками. `*` — распаковка списка.

**Пример:**
```
[Глава 1]
[Глава 2]
...
[Глава 20]
[⬅️ Назад] [Вперёд ➡️]
```

---

## Файл 9: `app/services/manga_service.py` — Бизнес-логика

Это связующее звено между обработчиками и парсером.

```python
class MangaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = RemangaParser()
        self.file_handler = FileHandler()
```

**Разбор:**
- `__init__` — конструктор. Вызывается при создании объекта.
- `self.db` — сохраняем сессию БД
- `self.parser = RemangaParser()` — создаем парсер
- `self.file_handler = FileHandler()` — создаем обработчик файлов

**Аналогия:** MangaService — это директор ресторана. Он не готовит сам (это делает парсер) и не моет посуду (это делает file_handler), но он всех координирует.

```python
    async def close(self):
        await self.parser.close()
```
**Что это:** Закрываем HTTP-сессию парсера.

### Проверка: уже скачано?

```python
    async def is_chapter_downloaded(self, user_id: int, manga_id: str, chapter_id: str) -> bool:
        result = await self.db.execute(
            select(DownloadedChapter).where(
                DownloadedChapter.user_id == user_id,
                DownloadedChapter.manga_id == manga_id,
                DownloadedChapter.chapter_id == chapter_id
            )
        )
        return result.scalar_one_or_none() is not None
```

**Разбор:**
- `select(DownloadedChapter)` — запрос к таблице `downloaded_chapters`
- `.where(...)` — три условия И (AND):
  - `user_id == user_id`
  - `manga_id == manga_id`
  - `chapter_id == chapter_id`
- `result.scalar_one_or_none()` — одна запись или None
- `is not None` — превращаем в `True`/`False`

### Отметить как скачанную

```python
    async def mark_chapter_downloaded(self, user_id: int, manga_id: str, chapter_id: str, chapter_number: float):
        downloaded = DownloadedChapter(
            user_id=user_id,
            manga_id=manga_id,
            chapter_id=chapter_id,
            chapter_number=chapter_number
        )
        self.db.add(downloaded)
        await self.db.commit()
```

**Разбор:**
- Создаем объект `DownloadedChapter`
- `self.db.add(downloaded)` — добавляем в сессию (пока только в памяти)
- `await self.db.commit()` — СОХРАНЯЕМ в БД. Без `commit` данные не запишутся!

### Скачивание главы (приватный метод)

```python
    async def _download_chapter(self, chapter_id: str, manga_title: str = None, chapter_num: float = None, compress: bool = False, progress_callback=None) -> str:
```

**Разбор параметров:**
- `chapter_id` — ID главы в Remanga
- `manga_title` — название манги (для имени файла)
- `chapter_num` — номер главы (для имени файла)
- `compress=False` — сжимать ли изображения
- `progress_callback` — функция для обновления прогресса

```python
        pages = await self.parser.get_chapter_pages(chapter_id)
        if not pages:
            raise Exception(f"No pages found for chapter {chapter_id}")
```
**Разбор:**
- Получаем список страниц
- `raise Exception(...)` — если страниц нет, создаем ошибку. Это прервет выполнение и перейдет к `except` в вызывающем коде.

```python
        temp_images = []
        for idx, page in enumerate(pages, 1):
            try:
                if progress_callback:
                    await progress_callback(idx, total_pages, "downloading")
                
                img_data = await self.parser.download_image(page.image_url)
                temp_path = await self.file_handler.save_temp_file(img_data, f"page_{page.number}.jpg")
```

**Разбор:**
- `enumerate(pages, 1)` — нумеруем страницы, начиная с 1
- `progress_callback(idx, total_pages, "downloading")` — обновляем прогресс
- `download_image(page.image_url)` — скачиваем байты картинки
- `save_temp_file(img_data, ...)` — сохраняем во временный файл

```python
                if compress:
                    compressed_path = await self.file_handler.compress_image(temp_path, quality=70)
                    temp_images.append(compressed_path)
                else:
                    temp_images.append(temp_path)
```
**Разбор:** Если `compress=True` — сжимаем изображение (quality=70) и сохраняем сжатую версию.

```python
        if progress_callback:
            await progress_callback(total_pages, total_pages, "creating_pdf")
```
**Что это:** Говорим: "Все страницы скачаны, теперь создаю PDF".

```python
        if manga_title and chapter_num is not None:
            safe_title = "".join(c for c in manga_title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title[:50]
            filename = f"{safe_title} - Глава {chapter_num}.pdf"
        else:
            filename = f"chapter_{chapter_id}.pdf"
```

**Разбор:**
- Очищаем название от недопустимых символов для Windows (убираем `\/:*?"<>|`)
- `c.isalnum()` — буква или цифра
- `safe_title[:50]` — не более 50 символов
- Формируем читаемое имя файла: `Наруто - Глава 15.pdf`

```python
        pdf_path = await self.file_handler.images_to_pdf(temp_images, filename)
```
**Что это:** Собираем все картинки в один PDF.

```python
        file_size = self.file_handler.check_file_size(pdf_path)
        if file_size > 50 * 1024 * 1024 and not compress:
            await self.file_handler.cleanup_temp_files(temp_images + [pdf_path])
            return await self._download_chapter(chapter_id, manga_title, chapter_num, compress=True, progress_callback=progress_callback)
```

**Разбор:**
- Проверяем размер PDF
- Если >50 МБ и мы еще не сжимали — удаляем все файлы и пересоздаем со сжатием!
- Это **рекурсия** — функция вызывает сама себя, но с другим параметром (`compress=True`)

```python
        await self.file_handler.cleanup_temp_files(temp_images)
        return pdf_path
```
**Что это:** Удаляем временные JPG-файлы (страницы) и возвращаем путь к PDF.

### Публичный метод скачивания

```python
    async def download_chapter(self, chapter_id: str, manga_id: str, manga_title: str, chapter_num: float, user_id: int, progress_callback=None) -> tuple[str, bool]:
        already_downloaded = await self.is_chapter_downloaded(user_id, manga_id, chapter_id)
        if already_downloaded:
            return None, True
        
        pdf_path = await self._download_chapter(chapter_id, manga_title, chapter_num, compress=False, progress_callback=progress_callback)
        await self.mark_chapter_downloaded(user_id, manga_id, chapter_id, chapter_num)
        return pdf_path, False
```

**Разбор:**
- Проверяем, не скачана ли глава
- Если скачана → возвращаем `(None, True)`
- Иначе скачиваем и отмечаем в БД
- Возвращаем `(путь_к_PDF, False)`

### Скачивание всех глав

```python
    async def download_all_chapters(self, manga_id: str, manga_title: str, user_tg_id: int) -> list[str]:
        chapters = await self.get_chapters(manga_id)
        semaphore = asyncio.Semaphore(3)

        async def download_with_limit(chapter: ChapterInfo):
            async with semaphore:
                try:
                    return await self._download_chapter(chapter.id, manga_title, chapter.number)
                except Exception as e:
                    logger.error(f"Failed to download chapter {chapter.id}: {e}")
                    return None

        tasks = [download_with_limit(ch) for ch in chapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, str)]
```

**Разбор:**
- `asyncio.Semaphore(3)` — семафор. Это как охранник у двери, который пропускает максимум 3 человека одновременно.
- Мы не хотим скачивать 1000 глав параллельно — забьем канал и нас забанит Remanga.
- Создаем список задач (по одной на каждую главу)
- `asyncio.gather(..., return_exceptions=True)` — запускаем все задачи параллельно. Если какая-то упадет с ошибкой — не падаем, а продолжаем остальные.

---

## Файл 10: `app/services/parsers/remanga.py` — Парсер Remanga

Этот файл общается с API remanga.org.

### Dataclasses

```python
@dataclass
class MangaTitleInfo:
    id: str
    title: str
    cover_url: str | None
    description: str | None
    year: int | None
    status: str | None
    chapters_count: int
```

**Что такое `@dataclass`?**
Это декоратор, который автоматически создает:
- `__init__` (конструктор)
- `__repr__` (красивый вывод)
- `__eq__` (сравнение)

**Аналогия:** Как будто ты написал бланк анкеты. `@dataclass` автоматически сделает из него полноценную форму с полями.

`str | None` означает "строка или None" (поле может быть пустым). Это синтаксис Python 3.11+, он короче чем `Optional[str]`.

### Инициализация парсера

```python
class RemangaParser:
    BASE_URL = "https://remanga.org"
    API_URL = "https://api.remanga.org/api"
    FLARESOLVERR_URL = "http://localhost:8191/v1"
```
**Разбор:**
- `BASE_URL` — основной сайт
- `API_URL` — API для запросов данных
- `FLARESOLVERR_URL` — локальный сервис для обхода Cloudflare (должен быть запущен отдельно)

```python
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
            "Accept": "application/json",
        }
        self.scraper = cloudscraper.create_scraper(...)
```

**Разбор:**
- `timeout=30` — ждем ответа не более 30 секунд
- `self.headers` — заголовки HTTP-запросов. Мы притворяемся браузером Chrome.
- `cloudscraper.create_scraper()` — создаем обходчик Cloudflare с эмуляцией Chrome на Windows.

### Ленивая сессия

```python
    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers,
                connector=aiohttp.TCPConnector(ssl=True)
            )
        return self.session
```

**Разбор:**
- "Ленивая" (lazy) инициализация — создаем сессию только когда она впервые понадобится
- Если сессия закрыта — создаем новую
- `TCPConnector(ssl=True)` — используем SSL (https)

### Поиск манги

```python
    async def search(self, query: str, limit: int = 10) -> list[MangaTitleInfo]:
        url = f"{self.API_URL}/search/"
        params = {"query": query}
```
**Что это:** Формируем URL: `https://api.remanga.org/api/search/?query=Наруто`

```python
        async with session.get(url, params=params) as response:
```
**Что это:** Отправляем GET-запрос. `async with` — сессия автоматически закроется.

```python
            data = await response.json()
            items = data.get("content", [])
```
**Разбор:**
- `response.json()` — парсим JSON-ответ
- `data.get("content", [])` — берем массив результатов. Если нет — пустой список.

```python
            for item in items:
                manga_dir = item.get("dir", "")
                title = item.get("rus_name") or item.get("en_name", "Unknown")
                relevance = self._calculate_relevance(query, title)
```
**Разбор:**
- `item.get("dir", "")` — берем поле `dir` (это и есть ID манги в Remanga)
- `item.get("rus_name") or item.get("en_name", "Unknown")` — если нет русского названия, берем английское. Если и его нет — "Unknown".

```python
                manga_info = MangaTitleInfo(
                    id=manga_dir,
                    title=title,
                    cover_url=f"https://remanga.org{item.get('img', {}).get('high')}" if item.get("img", {}).get("high") else None,
                    ...
                )
```
**Разбор:**
- `f"https://remanga.org{...}"` — формируем полный URL обложки
- `item.get('img', {}).get('high')` — безопасное вложенное получение. Если `img` нет — вернет `{}`, и `.get('high')` вернет `None`.

```python
            results_with_score.sort(key=lambda x: x[0], reverse=True)
```
**Что это:** Сортируем по релевантности. `reverse=True` — от большего к меньшему.

### Получение глав

```python
    async def get_chapters(self, manga_id: str, volume: int | None = None) -> list[ChapterInfo]:
        title = await self.get_title(manga_id)
        if not title:
            return []
```
**Что это:** Сначала получаем тайтл, чтобы узнать `branch_id` (ID перевода/ветки).

```python
        async with session.get(title_url) as response:
            data = await response.json()
            branches = data.get("content", {}).get("branches", [])
            branch_id = branches[0]["id"]
```
**Разбор:**
- `branches` — разные группы переводчиков могут переводить одну мангу
- Берем первую ветку (`branches[0]`)

```python
        while True:
            chapters_url = f"{self.API_URL}/titles/chapters/"
            params = {"branch_id": branch_id, "ordering": "index", "page": page, "count": 100}
            
            async with session.get(chapters_url, params=params) as ch_response:
                ch_data = await ch_response.json()
                content = ch_data.get("content", [])
                
                if not content:
                    break
                
                for item in content:
                    all_chapters.append(ChapterInfo(...))
                
                if len(content) < 100:
                    break
                
                page += 1
```

**Разбор:**
- `while True:` — бесконечный цикл
- Запрашиваем по 100 глав за раз (`count=100`)
- `ordering="index"` — сортировка по порядку
- `if not content: break` — если API вернул пустой список, заканчиваем
- `if len(content) < 100: break` — если получили меньше 100, значит это была последняя страница
- `page += 1` — переходим к следующей странице

**Аналогия:** Это как листать каталог. Ты просишь: "Дай страницу 1 по 100 товаров". Если получил 100 — значит есть еще. Просишь страницу 2. Когда получишь меньше 100 — останавливаешься.

### Получение страниц главы

```python
    async def get_chapter_pages(self, chapter_id: str) -> list[PageInfo]:
        url = f"{self.API_URL}/titles/chapters/{chapter_id}/"
```

```python
                page_list = chapter_data.get("pages", [])
                
                for idx, page in enumerate(page_list, start=1):
                    image_url = ""
                    
                    if isinstance(page, str):
                        image_url = page
                    elif isinstance(page, list):
                        if len(page) > 0:
                            first_item = page[0]
                            if isinstance(first_item, dict):
                                image_url = first_item.get("link", "")
                            elif isinstance(first_item, str):
                                image_url = first_item
                    elif isinstance(page, dict):
                        image_url = page.get("link") or page.get("url") or page.get("image", "")
```

**Разбор:**
- API Remanga возвращает страницы в разных форматах в зависимости от типа изображения
- `isinstance(page, str)` — если страница — просто строка (URL)
- `isinstance(page, list)` — если список (варианты качества), берем первый элемент
- `isinstance(page, dict)` — если словарь, ищем поле `link`, `url` или `image`

**Зачем так сложно?** Потому что API remanga.org меняет формат ответа. Это защита от изменений.

### Скачивание изображения

```python
    async def download_image(self, url: str, retry_count: int = 3) -> bytes:
        await asyncio.sleep(0.5)
```
**Что это:** Ждем 0.5 секунды между запросами. Это **rate limiting** — чтобы нас не забанили за слишком частые запросы.

```python
        for attempt in range(retry_count):
            try:
                session = await self._get_session()
                
                image_headers = {
                    "User-Agent": "...",
                    "Referer": "https://remanga.org/",
                    "Origin": "https://remanga.org",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    ...
                }
```

**Разбор:**
- Цикл `for attempt in range(retry_count)` — максимум 3 попытки
- `Referer` — говорим сайту: "Мы пришли со страницы remanga.org" (без этого могут отказать)
- `Origin` — то же самое
- `Accept` — какие форматы изображений мы принимаем

```python
                async with session.get(url, headers=image_headers, allow_redirects=True) as response:
                    if response.status == 200:
                        content = await response.read()
                        return content
                    
                    if response.status == 403:
                        return await self._download_with_cloudscraper(url)
```

**Разбор:**
- `allow_redirects=True` — следовать за перенаправлениями
- `response.status == 200` — успех! Возвращаем байты.
- `response.status == 403` — доступ запрещен (Cloudflare блокирует). Переключаемся на `cloudscraper`.

```python
            except Exception as e:
                if "403" in str(e) or "Cloudflare" in str(e):
                    return await self._download_with_cloudscraper(url)
                
                if attempt == retry_count - 1:
                    raise
                
                delay = 2 * (attempt + 1)
                await asyncio.sleep(delay)
```

**Разбор:**
- Если ошибка связана с Cloudflare — пробуем `cloudscraper`
- Если это последняя попытка — поднимаем ошибку (программа упадет, но `except` в `callbacks.py` ее поймает)
- Иначе — ждем: 2 секунды, 4 секунды, 6 секунды (экспоненциальная задержка)

### Cloudscraper (обход Cloudflare)

```python
    async def _download_with_cloudscraper(self, url: str) -> bytes:
        def sync_download():
            response = self.scraper.get(url, headers={...})
            if response.status_code != 200:
                raise Exception(f"Cloudscraper failed with status {response.status_code}")
            return response.content
        
        content = await asyncio.to_thread(sync_download)
        return content
```

**Разбор:**
- `cloudscraper` — синхронная библиотека (не умеет `await`)
- `asyncio.to_thread(sync_download)` — запускаем синхронную функцию в отдельном потоке, чтобы не блокировать основной цикл
- `self.scraper.get(...)` — cloudscraper сам решает загадки Cloudflare и получает картинку

---

## Файл 11: `app/utils/callback_manager.py` — Менеджер callback'ов

Этот файл решает проблему: callback_data в Telegram ограничен 64 байтами, а наши ID могут быть длиннее.

```python
class CallbackManager:
    @staticmethod
    def _generate_short_id(user_id: int, data_type: str, full_data: str) -> str:
        content = f"{user_id}:{data_type}:{full_data}:{datetime.utcnow().timestamp()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
```

**Разбор:**
- `@staticmethod` — метод, который не использует `self`. Можно вызвать как `CallbackManager._generate_short_id(...)`.
- `f"{user_id}:{data_type}:{full_data}:{timestamp}"` — склеиваем данные в строку
- `hashlib.md5(content.encode())` — вычисляем MD5-хеш
- `.hexdigest()[:16]` — берем первые 16 символов хеша

**Почему MD5?** Потому что он дает фиксированную длину (32 символа) и быстро считается. Коллизии (когда два разных набора данных дают один хеш) маловероятны при использовании timestamp.

```python
    @staticmethod
    async def create_callback(db, user_id, data_type, data):
        full_data = json.dumps(data, ensure_ascii=False)
        short_id = CallbackManager._generate_short_id(user_id, data_type, full_data)
        
        result = await db.execute(
            select(CallbackData).where(CallbackData.short_id == short_id)
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            callback_data = CallbackData(
                short_id=short_id,
                user_id=user_id,
                data_type=data_type,
                full_data=full_data
            )
            db.add(callback_data)
            await db.commit()
        
        return short_id
```

**Разбор:**
- `json.dumps(data, ensure_ascii=False)` — превращаем словарь в JSON-строку
- Проверяем, есть ли уже такой `short_id` в БД (дедупликация)
- Если нет — создаем запись
- Возвращаем `short_id` (16 символов, укладывается в лимит Telegram!)

```python
    @staticmethod
    async def get_callback_data(db, short_id, user_id):
        result = await db.execute(
            select(CallbackData).where(
                CallbackData.short_id == short_id,
                CallbackData.user_id == user_id
            )
        )
        callback_data = result.scalar_one_or_none()
        
        if callback_data:
            return json.loads(callback_data.full_data)
        return None
```

**Разбор:**
- Ищем по `short_id` И `user_id` (двойная проверка безопасности)
- `json.loads(...)` — превращаем JSON-строку обратно в словарь Python

---

## Файл 12: `app/utils/file_handler.py` — Работа с файлами

```python
class FileHandler:
    def __init__(self, downloads_dir: str = "downloads"):
        self.downloads_dir = downloads_dir
        os.makedirs(downloads_dir, exist_ok=True)
```
**Разбор:**
- `os.makedirs(..., exist_ok=True)` — создаем папку "downloads", если ее еще нет. `exist_ok=True` значит "не падай, если папка уже есть".

### Сохранение временного файла

```python
    async def save_temp_file(self, content: bytes, filename: str) -> str:
        filepath = os.path.join(self.downloads_dir, filename)
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        return filepath
```

**Разбор:**
- `os.path.join(...)` — склеиваем путь: `downloads/page_1.jpg`
- `aiofiles.open(..., "wb")` — открываем файл для записи байтов (асинхронно!)
- `await f.write(content)` — пишем байты
- **Почему `aiofiles`?** Обычное `open()` блокирует программу на время записи. `aiofiles` позволяет другим задачам работать параллельно.

### Создание PDF

```python
    async def images_to_pdf(self, image_paths: list[str], output_filename: str) -> str:
        output_path = os.path.join(self.downloads_dir, output_filename)
        
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_paths))
        
        return output_path
```

**Разбор:**
- `img2pdf.convert(image_paths)` — библиотека `img2pdf` собирает картинки в PDF
- `with open(..., "wb")` — открываем файл, пишем байты PDF
- Тут используется обычное `open()`, потому что `img2pdf` тоже синхронная, и разницы нет

### Сжатие изображения

```python
    async def compress_image(self, image_path: str, quality: int = None) -> str:
        if quality is None:
            quality = config.COMPRESSION_QUALITY
        
        output_path = image_path.replace(".jpg", "_compressed.jpg")
        
        with Image.open(image_path) as img:
            if max(img.size) > config.MAX_IMAGE_DIMENSION:
                img.thumbnail((config.MAX_IMAGE_DIMENSION, config.MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
            
            img.save(output_path, "JPEG", quality=quality, optimize=True)
        
        return output_path
```

**Разбор:**
- `Image.open(image_path)` — открываем картинку через Pillow
- `max(img.size)` — большая сторона картинки (ширина или высота)
- `img.thumbnail(..., Image.Resampling.LANCZOS)` — уменьшаем, сохраняя пропорции. `LANCZOS` — качественный алгоритм ресайза.
- `img.save(..., quality=quality, optimize=True)` — сохраняем с заданным качеством

### Проверка размера

```python
    def check_file_size(self, filepath: str) -> int:
        return os.path.getsize(filepath)
```
**Что это:** Синхронная функция. Возвращает размер файла в байтах.

### Очистка

```python
    async def cleanup_temp_files(self, filepaths: list[str]):
        for path in filepaths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {e}")
```
**Разбор:**
- Проходим по списку файлов
- `os.path.exists(path)` — проверяем, существует ли файл
- `os.remove(path)` — удаляем
- `try/except` — если не удалось удалить (например, файл занят другой программой), логируем и продолжаем

---

## Итог: как всё связано

| Ты нажимаешь | Что происходит | Какой файл задействован |
|-------------|----------------|------------------------|
| `/start` | Бот приветствует и показывает меню | `commands.py` → `inline.py` |
| "🔍 Поиск манги" | Устанавливается состояние ожидания | `manga.py` |
| Пишешь "Наруто" | Идет поиск через API Remanga | `manga.py` → `manga_service.py` → `remanga.py` |
| Нажимаешь результат | Загружается карточка с обложкой | `manga.py` → `manga_service.py` → `remanga.py` |
| "По главам" | Загружается список глав | `callbacks.py` → `remanga.py` → `inline.py` |
| "Глава 15" | Проверка БД → скачивание → прогресс → PDF → отправка | `callbacks.py` → `manga_service.py` → `remanga.py` → `file_handler.py` |
| Файл приходит | Статистика обновляется в БД | `callbacks.py` → `manga_service.py` → `database.py` |

---

## Полезные термины (глоссарий)

| Термин | Объяснение |
|--------|-----------|
| **async/await** | Способ делать несколько дел одновременно. Когда ждем ответа от интернета, программа не зависает, а занимается другими задачами. |
| **await** | "Подожди здесь, пока это закончится, но не мешай другим работать". |
| **try/except/finally** | "Попробуй сделать это. Если не получится — сделай то. В любом случае сделай это в конце". |
| **return** | "Верни результат и закончи работу функции". |
| **break** | "Выйди из цикла прямо сейчас". |
| **continue** | "Пропусти оставшуюся часть итерации и перейди к следующей". |
| **f-string** | `f"Привет, {name}"` — способ вставить переменные в строку. |
| **list comprehension** | `[x*2 for x in numbers]` — короткий способ создать список. |
| **lambda** | Анонимная (безымянная) функция. `lambda x: x.number` значит "функция, которая для x возвращает x.number". |
| **dictionary (dict)** | `{"ключ": "значение"}` — структура данных для хранения пар ключ-значение. |
| **ORM** | Object-Relational Mapping. Переводит между Python-объектами и SQL-таблицами. |
| **SQL** | Язык запросов к базам данных. |
| **HTTP** | Протокол передачи данных в интернете. |
| **API** | Интерфейс программирования приложений. Способ общения программ друг с другом. |
| **JSON** | Формат текста для передачи данных. Похож на словарь Python. |
| **Hash (хеш)** | "Отпечаток" данных. Из большого текста получается короткая строка фиксированной длины. |
| **MD5** | Алгоритм хеширования. Дает 32-символьную строку. |
| **Semaphore** | Счетчик разрешений. "Максимум N задач одновременно". |
| **Singleton** | Паттерн, когда объект создается только один раз и используется везде. |
| **Lazy initialization** | Создание объекта только при первом обращении. |
| **Rate limiting** | Искусственное замедление запросов, чтобы не перегружать сервер. |

