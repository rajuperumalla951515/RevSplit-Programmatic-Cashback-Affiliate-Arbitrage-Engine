-- Copy of schema/001_initial_schema.sql
-- Complete PostgreSQL Local DDL Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE user_status AS ENUM ('ACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION');
CREATE TYPE click_status AS ENUM ('INITIATED', 'REDIRECTED', 'CONVERTED', 'EXPIRED');
CREATE TYPE transaction_status AS ENUM ('PENDING', 'VERIFIED', 'REJECTED', 'PAIDOUT');
CREATE TYPE ledger_entry_type AS ENUM ('DEBIT', 'CREDIT');
CREATE TYPE ledger_category AS ENUM (
    'CASHBACK_PENDING',
    'CASHBACK_VERIFIED',
    'PLATFORM_REVENUE',
    'CASHOUT_WITHDRAWAL',
    'REVERSAL_ADJUSTMENT'
);
CREATE TYPE payout_status AS ENUM ('REQUESTED', 'PROCESSING', 'COMPLETED', 'FAILED');

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    status user_status NOT NULL DEFAULT 'ACTIVE',
    country_code VARCHAR(3) DEFAULT 'IND',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wallets (
    wallet_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    pending_balance NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (pending_balance >= 0),
    available_balance NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (available_balance >= 0),
    locked_balance NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (locked_balance >= 0),
    total_cashback_earned NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (total_cashback_earned >= 0),
    total_withdrawn NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (total_withdrawn >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE merchants (
    merchant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    base_url VARCHAR(512) NOT NULL,
    affiliate_template_url VARCHAR(1024) NOT NULL,
    webhook_secret VARCHAR(255) NOT NULL,
    user_cashback_percentage NUMERIC(5, 2) NOT NULL DEFAULT 70.00 CHECK (user_cashback_percentage BETWEEN 0 AND 100),
    platform_revenue_percentage NUMERIC(5, 2) NOT NULL DEFAULT 30.00 CHECK (platform_revenue_percentage BETWEEN 0 AND 100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_split_sum CHECK (user_cashback_percentage + platform_revenue_percentage = 100.00)
);

CREATE TABLE click_logs (
    click_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub_id VARCHAR(64) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id) ON DELETE RESTRICT,
    original_url TEXT NOT NULL,
    affiliate_redirect_url TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    status click_status NOT NULL DEFAULT 'INITIATED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE affiliate_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub_id VARCHAR(64) NOT NULL REFERENCES click_logs(sub_id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id) ON DELETE RESTRICT,
    merchant_transaction_id VARCHAR(128) NOT NULL,
    gross_sale_amount NUMERIC(14, 4) NOT NULL CHECK (gross_sale_amount >= 0),
    gross_commission_amount NUMERIC(14, 4) NOT NULL CHECK (gross_commission_amount >= 0),
    user_cashback_amount NUMERIC(14, 4) NOT NULL CHECK (user_cashback_amount >= 0),
    platform_revenue_amount NUMERIC(14, 4) NOT NULL CHECK (platform_revenue_amount >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    status transaction_status NOT NULL DEFAULT 'PENDING',
    raw_postback_payload JSONB,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_merchant_transaction UNIQUE (merchant_id, merchant_transaction_id),
    CONSTRAINT chk_commission_split CHECK (user_cashback_amount + platform_revenue_amount = gross_commission_amount)
);

CREATE TABLE wallet_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id UUID NOT NULL REFERENCES wallets(wallet_id) ON DELETE RESTRICT,
    transaction_id UUID REFERENCES affiliate_transactions(transaction_id) ON DELETE RESTRICT,
    entry_type ledger_entry_type NOT NULL,
    category ledger_category NOT NULL,
    amount NUMERIC(14, 4) NOT NULL CHECK (amount > 0),
    balance_after NUMERIC(14, 4) NOT NULL CHECK (balance_after >= 0),
    description VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION enforce_ledger_immutability()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'CRITICAL SECURITY VIOLATION: Wallet ledger records are immutable and cannot be updated or deleted!';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_protect_ledger_updates
BEFORE UPDATE OR DELETE ON wallet_ledger
FOR EACH ROW EXECUTE FUNCTION enforce_ledger_immutability();
