"""
Tests for loan_api endpoints.
All DB calls are mocked — no real database needed to run tests.
Run with:  cd backend && pytest tests/ -v
"""
import pytest
from unittest.mock import patch
from conftest import (
    make_mock_conn,
    FAKE_SUMMARY_ROW, FAKE_SUMMARY_COLS,
    FAKE_CUSTOMER_ROW, FAKE_CUSTOMER_COLS,
)


# ══ Health ════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_ok(self, client):
        conn, cur = make_mock_conn(fetchone=(1,))
        cur.description = [type("C", (), {"name": "v"})()]
        with patch("main.get_connection", return_value=conn):
            r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["database"] == "connected"

    def test_health_db_down(self, client):
        with patch("main.get_connection", side_effect=Exception("DB unavailable")):
            r = client.get("/health")
        assert r.status_code == 503
        assert "unavailable" in r.json()["detail"].lower()

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "running" in r.json()["message"].lower()


# ══ Summary ═══════════════════════════════════════════════════════════════════

class TestSummary:
    def _mock(self, client):
        conn, cur = make_mock_conn(fetchone=FAKE_SUMMARY_ROW, cols=FAKE_SUMMARY_COLS)
        with patch("main.get_connection", return_value=conn):
            return client.get("/api/summary")

    def test_returns_200(self, client):
        assert self._mock(client).status_code == 200

    def test_fields_present(self, client):
        data = self._mock(client).json()
        for field in ("total", "active", "arrears", "arrears_rate", "total_portfolio", "avg_days_overdue"):
            assert field in data, f"Missing field: {field}"

    def test_arrears_rate_calculated(self, client):
        data = self._mock(client).json()
        expected = round(389 / 421 * 100, 1)
        assert data["arrears_rate"] == expected

    def test_avg_days_overdue_rounded(self, client):
        data = self._mock(client).json()
        assert isinstance(data["avg_days_overdue"], int)

    def test_db_error_returns_500(self, client):
        with patch("main.get_connection", side_effect=Exception("boom")):
            r = client.get("/api/summary")
        assert r.status_code == 500


# ══ Customers ═════════════════════════════════════════════════════════════════

class TestCustomers:
    def _mock(self, client, rows=None, **params):
        rows = rows if rows is not None else [FAKE_CUSTOMER_ROW]
        conn, cur = make_mock_conn(fetchall=rows, cols=FAKE_CUSTOMER_COLS)
        with patch("main.get_connection", return_value=conn):
            return client.get("/api/customers", params=params)

    def test_returns_200(self, client):
        assert self._mock(client).status_code == 200

    def test_response_shape(self, client):
        data = self._mock(client).json()
        assert "total" in data
        assert "customers" in data
        assert isinstance(data["customers"], list)

    def test_total_matches_list_length(self, client):
        data = self._mock(client).json()
        assert data["total"] == len(data["customers"])

    def test_customer_fields(self, client):
        customer = self._mock(client).json()["customers"][0]
        for field in ("account_key", "full_name", "phone", "status", "days_overdue"):
            assert field in customer

    def test_empty_result(self, client):
        data = self._mock(client, rows=[]).json()
        assert data["total"] == 0
        assert data["customers"] == []

    def test_search_param_passed(self, client):
        conn, cur = make_mock_conn(fetchall=[FAKE_CUSTOMER_ROW], cols=FAKE_CUSTOMER_COLS)
        with patch("main.get_connection", return_value=conn):
            r = client.get("/api/customers", params={"search": "abeba"})
        assert r.status_code == 200
        # Verify LIKE clause was used
        call_args = cur.execute.call_args
        assert "%abeba%" in str(call_args)

    def test_status_filter_active(self, client):
        conn, cur = make_mock_conn(fetchall=[], cols=FAKE_CUSTOMER_COLS)
        with patch("main.get_connection", return_value=conn):
            r = client.get("/api/customers", params={"status": "ACTIVE"})
        assert r.status_code == 200
        call_args = cur.execute.call_args
        assert "ACTIVE" in str(call_args)

    def test_status_filter_arrears(self, client):
        conn, cur = make_mock_conn(fetchall=[], cols=FAKE_CUSTOMER_COLS)
        with patch("main.get_connection", return_value=conn):
            r = client.get("/api/customers", params={"status": "ARREARS"})
        assert r.status_code == 200

    def test_invalid_status_ignored(self, client):
        """Invalid status values should not be passed to DB."""
        conn, cur = make_mock_conn(fetchall=[], cols=FAKE_CUSTOMER_COLS)
        with patch("main.get_connection", return_value=conn):
            r = client.get("/api/customers", params={"status": "HACKED; DROP TABLE"})
        assert r.status_code == 200
        assert "HACKED" not in str(cur.execute.call_args)

    def test_sort_injection_blocked(self, client):
        """SQL injection via sort_by must be blocked by allowlist."""
        conn, cur = make_mock_conn(fetchall=[], cols=FAKE_CUSTOMER_COLS)
        with patch("main.get_connection", return_value=conn):
            r = client.get("/api/customers", params={"sort_by": "1; DROP TABLE customers--"})
        assert r.status_code == 200
        # Falls back to default sort (days_overdue), not the injected value
        assert "DROP TABLE" not in str(cur.execute.call_args)

    def test_db_error_returns_500(self, client):
        with patch("main.get_connection", side_effect=Exception("boom")):
            r = client.get("/api/customers")
        assert r.status_code == 500

    def test_date_fields_serialized_as_strings(self, client):
        customer = self._mock(client).json()["customers"][0]
        assert isinstance(customer["disbursement_date"], str)
