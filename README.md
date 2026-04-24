# Telegram бот для скачивания манги

## Установка
1. Клонировать репозиторий
2. ``pip install -r requirements.txt``
3. Настроить .env с BOT_TOKEN(изменить на собственный)
4. python run_bot.py или start_bot.bat


### 1. Клонирование
``git clone <repo>``
``cd telegram-bot``

### 2. Установка зависимостей
``pip install -r requirements.txt``

### 3. Настройка .env
``echo BOT_TOKEN=ваш_токен > .env``
``echo USE_SQLITE=true >> .env``

### 4. Инициализация БД
``python -c "import asyncio; from app.models.database import init_db; asyncio.run(init_db())"``

### 5. Запуск
``python run_bot.py`` или start_bot.bat
