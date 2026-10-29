# English in Pocket

Telegram-бот для изучения английского на aiogram 3: учебные курсы с карточками и квизами, входной тест уровня, сохранение прогресса пользователя.

## Возможности
- 20 учебных модулей: грамматика (A1-A2, B1-B2, C1), глаголы (A1-A2, B1-B2, C1), неправильные и модальные глаголы, глагольные конструкции, фразовые глаголы, идиомы, коллокации, словообразование, тест уровня
- Прогресс, попытки и ответы пользователя по каждому курсу хранятся в базе

## Стек
Python, aiogram 3, SQLAlchemy 2 (async) + aiosqlite, python-dotenv, pytest, Docker, GitHub Actions

## Структура
```
app/          пакет бота: config, main, database, handlers, keyboards, modules (курсы)
tests/        тесты (pytest)
deployment/   systemd-юнит для запуска на Linux-сервере
scripts/      скрипт миграции базы
run.py        точка входа
```

## Запуск
```
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env        # впиши BOT_TOKEN (Linux/macOS: cp)
python run.py
```

## Docker
```
cp .env.example .env
docker compose up -d --build
```
База хранится в `./data/bot_database.db` и переживает перезапуски.

## Тесты
```
pip install -r requirements-dev.txt
python -m pytest -q
```

## Развёртывание на сервере
Юнит `deployment/english-bot.service` запускает бота как systemd-сервис с автоперезапуском; секреты берутся из `EnvironmentFile`. CI (GitHub Actions) гоняет линтер, тесты и сборку Docker-образа на каждый push.
