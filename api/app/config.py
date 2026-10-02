import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

# 生产环境（docker-compose）会直接注入 DATABASE_URL 和 REDIS_URL
# 开发环境会从 .env 读取 DB_HOST 等变量并拼接
load_dotenv(BACKEND_DIR / ".env")

# 优先使用 docker-compose 注入的 DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME = os.getenv("DB_NAME", "reborn")
    DATABASE_URL = (
        f"postgresql+asyncpg://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

# 优先使用 docker-compose 注入的 REDIS_URL
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) or None
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL = (
        f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        if REDIS_PASSWORD
        else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )

REDIS_SESSION_TTL = int(os.getenv("REDIS_SESSION_TTL", "86400"))

UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

STATIC_URL = "/api/static"

KICK_REASON_KEY_PREFIX = "reborn-kick-"