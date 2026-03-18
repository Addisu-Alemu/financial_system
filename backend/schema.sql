-- Run this first to create the table
CREATE TABLE IF NOT EXISTS customers (
    account_key       VARCHAR(60) PRIMARY KEY,
    full_name         VARCHAR(120) NOT NULL,
    phone             VARCHAR(40),
    disbursement_date DATE,
    loan_amount       BIGINT,
    modality          VARCHAR(20),
    num_payments      INTEGER,
    first_overdue_date DATE,
    days_overdue      INTEGER DEFAULT 0,
    status            VARCHAR(10) NOT NULL DEFAULT 'ACTIVE',
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- Index for fast search and filtering
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
CREATE INDEX IF NOT EXISTS idx_customers_name   ON customers(LOWER(full_name));
