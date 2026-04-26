# Telegram бот для скачивания манги

Telegram бот для поиска и скачивания манги с различных источников. Поддерживает скачивание глав в формате PDF.

## Возможности

- Поиск манги по названию
- Просмотр информации о манге
- Скачивание глав в PDF формате
- Поддержка парсера Remanga
- База данных для хранения истории

## Требования

- Python 3.10+
- pip (менеджер пакетов Python)
- Telegram Bot Token (получить у [@BotFather](https://t.me/botfather))

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/Whizyatinka/ultraprojectfinalversion.git
cd ultraprojectfinalversion
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

Или с использованием виртуального окружения (рекомендуется):

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=ваш_токен_от_botfather
USE_SQLITE=true
DATABASE_URL=sqlite:///telegram_bot.db
```

Или через командную строку:

**Windows (PowerShell):**
```powershell
echo BOT_TOKEN=ваш_токен > .env
echo USE_SQLITE=true >> .env
```

**Linux/Mac:**
```bash
echo "BOT_TOKEN=ваш_токен" > .env
echo "USE_SQLITE=true" >> .env
```

### 4. Инициализация базы данных

База данных создается автоматически при первом запуске. Если нужно создать вручную:

```bash
python -c "import asyncio; from app.models.database import init_db; asyncio.run(init_db())"
```

### 5. Запуск бота

**Windows:**
```bash
start_bot.bat
```
или
```bash
python run_bot.py
```

**Linux/Mac:**
```bash
python run_bot.py
```

## Использование Docker

### Сборка и запуск

```bash
docker-compose up -d
```

### Остановка

```bash
docker-compose down
```

## Структура проекта

```
telegram-bot/
├── app/
│   ├── handlers/          # Обработчики команд и callback'ов
│   ├── keyboards/         # Клавиатуры бота
│   ├── models/           # Модели базы данных
│   ├── services/         # Бизнес-логика и парсеры
│   └── utils/            # Вспомогательные функции
├── downloads/            # Скачанные файлы
├── .env                  # Переменные окружения
├── requirements.txt      # Зависимости Python
├── run_bot.py           # Точка входа
└── docker-compose.yml   # Docker конфигурация
```

## Команды бота

- `/start` - Запуск бота
- `/help` - Помощь
- Отправьте название манги для поиска

## Разработка

### Установка зависимостей для разработки

```bash
pip install -r requirements.txt
```

### Запуск в режиме разработки

```bash
python run_bot.py
```

## Troubleshooting

**Ошибка: "No module named 'aiogram'"**
```bash
pip install -r requirements.txt
```

**Ошибка: "Unauthorized"**
- Проверьте правильность BOT_TOKEN в .env файле

**Бот не отвечает:**
- Убедитесь, что бот запущен
- Проверьте интернет-соединение
- Проверьте логи на наличие ошибок

## Лицензия

MIT

## Автор

[@Whizyatinka](https://github.com/Whizyatinka)
