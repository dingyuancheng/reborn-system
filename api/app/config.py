import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "reborn")

DATABASE_URL = (
    f"postgresql+asyncpg://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) or None
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_SESSION_TTL = int(os.getenv("REDIS_SESSION_TTL", "86400"))

UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

STATIC_URL = "/static"

KICK_REASON_KEY_PREFIX = "reborn-kick-"