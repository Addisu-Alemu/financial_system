import os
import logging
import time
import psycopg2
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


def get_connection(retries: int = 5, delay: int = 2):
    """Open a fresh connection each request — simple and reliable."""
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.autocommit = True
            return conn
        except Exception as e:
            logger.warning(f"DB connect attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    raise RuntimeError("Could not connect to database after multiple attempts")