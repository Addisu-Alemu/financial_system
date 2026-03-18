import os
import logging
import time
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("loan_api.db")

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "postgres"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

# Connection pool — reuses connections instead of opening a new one per request
_pool = None


def _create_pool(retries: int = 5, delay: int = 3):
    """Create pool with retries — important when Docker starts backend before DB is ready."""
    global _pool
    for attempt in range(1, retries + 1):
        try:
            _pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, **DB_CONFIG)
            logger.info(f"Connection pool created (attempt {attempt})")
            return
        except Exception as e:
            logger.warning(f"DB not ready (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay)
    raise RuntimeError("Could not connect to database after multiple attempts")


def get_connection():
    """Get a connection from the pool, creating the pool on first call."""
    global _pool
    if _pool is None:
        _create_pool()
    conn = _pool.getconn()
    conn.autocommit = True
    return conn


def release_connection(conn):
    """Return a connection to the pool."""
    global _pool
    if _pool and conn:
        _pool.putconn(conn)
