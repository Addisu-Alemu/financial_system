import logging
import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
from database import get_connection

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("loan_api")


# ── Startup / shutdown ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loan Portfolio API starting up")
    try:
        conn = get_connection()
        conn.close()
        logger.info("Database connection: OK")
    except Exception as e:
        logger.error(f"Database connection FAILED on startup: {e}")
    yield
    logger.info("Loan Portfolio API shutting down")


# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Loan Portfolio API",
    description="Customer loan status and arrears tracking",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health():
    """Docker and monitoring use this to verify the service is alive."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/", tags=["system"])
def root():
    return {"message": "Loan Portfolio API is running", "docs": "/docs"}


# ── Summary ──────────────────────────────────────────────────────────────────
@app.get("/api/summary", tags=["customers"])
def get_summary():
    logger.info("GET /api/summary")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*)                                                AS total,
                SUM(CASE WHEN status = 'ACTIVE'  THEN 1 ELSE 0 END)   AS active,
                SUM(CASE WHEN status = 'ARREARS' THEN 1 ELSE 0 END)   AS arrears,
                SUM(loan_amount)                                        AS total_portfolio,
                AVG(CASE WHEN days_overdue > 0 THEN days_overdue END)  AS avg_days_overdue
            FROM customers
        """)
        row  = cur.fetchone()
        cols = [d[0] for d in cur.description]
        cur.close()
        conn.close()

        result = dict(zip(cols, row))
        result["arrears_rate"]     = round(result["arrears"] / result["total"] * 100, 1) if result["total"] else 0
        result["total_portfolio"]  = float(result["total_portfolio"] or 0)
        result["avg_days_overdue"] = round(float(result["avg_days_overdue"] or 0))
        logger.info(f"Summary: {result['total']} customers, {result['arrears']} in arrears")
        return result

    except Exception as e:
        logger.error(f"Error in /api/summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch summary")


# ── Customers ─────────────────────────────────────────────────────────────────
ALLOWED_SORTS = {
    "full_name", "account_key", "disbursement_date",
    "loan_amount", "days_overdue", "status",
}


@app.get("/api/customers", tags=["customers"])
def get_customers(
    search:   Optional[str] = Query(None),
    status:   Optional[str] = Query(None),
    sort_by:  Optional[str] = Query("days_overdue"),
    sort_dir: Optional[str] = Query("desc"),
):
    logger.info(f"GET /api/customers search={search!r} status={status!r}")
    try:
        conn   = get_connection()
        cur    = conn.cursor()
        query  = """
            SELECT account_key, full_name, phone, disbursement_date, loan_amount,
                   modality, num_payments, first_overdue_date, days_overdue, status
            FROM customers WHERE 1=1
        """
        params = []

        if search:
            query += " AND (LOWER(full_name) LIKE %s OR account_key LIKE %s OR phone LIKE %s)"
            like   = f"%{search.lower()}%"
            params.extend([like, like, like])

        if status and status.upper() in ("ACTIVE", "ARREARS"):
            query += " AND status = %s"
            params.append(status.upper())

        col       = sort_by if sort_by in ALLOWED_SORTS else "days_overdue"
        direction = "DESC" if sort_dir == "desc" else "ASC"
        query    += f" ORDER BY {col} {direction}"

        cur.execute(query, params)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        cur.close()
        conn.close()

        customers = []
        for row in rows:
            record = dict(zip(cols, row))
            for field in ("disbursement_date", "first_overdue_date"):
                if record[field]:
                    record[field] = str(record[field])
            customers.append(record)

        logger.info(f"Returned {len(customers)} customers")
        return {"total": len(customers), "customers": customers}

    except Exception as e:
        logger.error(f"Error in /api/customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customers")
