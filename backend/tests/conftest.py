"""
Shared fixtures for all tests.
Uses a real PostgreSQL connection (same DB, isolated with transactions that roll back).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


# ── Fake DB rows used across tests ───────────────────────────────────────────
FAKE_SUMMARY_ROW = (421, 32, 389, 150000000, 485.3)
FAKE_SUMMARY_COLS = [
    type("Col", (), {"name": n})()
    for n in ("total", "active", "arrears", "total_portfolio", "avg_days_overdue")
]

FAKE_CUSTOMER_ROW = (
    "0303/0020040/001/0501/002",
    "ABEBA ADDIS KEBEDE",
    "0911085712",
    "2024-11-23",
    1000000,
    "Quartely",
    16,
    "2025-02-22",
    389,
    "ARREARS",
)
FAKE_CUSTOMER_COLS = [
    type("Col", (), {"name": n})()
    for n in (
        "account_key", "full_name", "phone", "disbursement_date",
        "loan_amount", "modality", "num_payments", "first_overdue_date",
        "days_overdue", "status",
    )
]


def make_mock_conn(fetchone=None, fetchall=None, cols=None):
    """Build a mock psycopg2 connection/cursor pair."""
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone
    mock_cur.fetchall.return_value = fetchall or []
    mock_cur.description = cols or []

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


@pytest.fixture
def client():
    """FastAPI test client — imports app fresh each time."""
    from main import app
    return TestClient(app)
