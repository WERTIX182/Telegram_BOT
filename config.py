import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot_database.db")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

config = Config()
