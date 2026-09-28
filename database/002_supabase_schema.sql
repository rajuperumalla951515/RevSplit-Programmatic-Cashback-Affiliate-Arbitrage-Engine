-- Copy of schema/002_supabase_schema.sql for Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE TYPE user_status AS ENUM ('ACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE click_status AS ENUM ('INITIATED', 'REDIRECTED', 'CONVERTED', 'EXPIRED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE transaction_status AS ENUM ('PENDING', 'VERIFIED', 'REJECTED', 'PAIDOUT');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE ledger_entry_type AS ENUM ('DEBIT', 'CREDIT');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE ledger_category AS ENUM (
        'CASHBACK_PENDING',
        'CASHBACK_VERIFIED',
        'PLATFORM_REVENUE',
        'CASHOUT_WITHDRAWAL',
        'REVERSAL_ADJUSTMENT'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE payout_status AS ENUM ('REQUESTED', 'PROCESSING', 'COMPLETED', 'FAILED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS public.users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) DEFAULT '',
    full_name VARCHAR(120) NOT NULL,
    status user_status NOT NULL DEFAULT 'ACTIVE',
    country_code VARCHAR(3) DEFAULT 'IND',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.wallets (
    wallet_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    pending_balance NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (pending_balance >= 0),
    available_balance NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (available_balance >= 0),
    locked_balance NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (locked_balance >= 0),
    total_cashback_earned NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (total_cashback_earned >= 0),
    total_withdrawn NUMERIC(14, 4) NOT NULL DEFAULT 0.0000 CHECK (total_withdrawn >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.merchants (
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

CREATE TABLE IF NOT EXISTS public.click_logs (
    click_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub_id VARCHAR(64) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES public.merchants(merchant_id) ON DELETE RESTRICT,
    original_url TEXT NOT NULL,
    affiliate_redirect_url TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    status click_status NOT NULL DEFAULT 'INITIATED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.affiliate_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub_id VARCHAR(64) NOT NULL REFERENCES public.click_logs(sub_id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    merchant_id UUID NOT NULL REFERENCES public.merchants(merchant_id) ON DELETE RESTRICT,
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

CREATE TABLE IF NOT EXISTS public.wallet_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id UUID NOT NULL REFERENCES public.wallets(wallet_id) ON DELETE RESTRICT,
    transaction_id UUID REFERENCES public.affiliate_transactions(transaction_id) ON DELETE RESTRICT,
    entry_type ledger_entry_type NOT NULL,
    category ledger_category NOT NULL,
    amount NUMERIC(14, 4) NOT NULL CHECK (amount > 0),
    balance_after NUMERIC(14, 4) NOT NULL CHECK (balance_after >= 0),
    description VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION process_commission_postback(
    p_sub_id VARCHAR(64),
    p_merchant_transaction_id VARCHAR(128),
    p_gross_sale NUMERIC(14, 4),
    p_gross_commission NUMERIC(14, 4),
    p_currency VARCHAR(3),
    p_raw_payload JSONB
)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
    v_merchant_id UUID;
    v_wallet_id UUID;
    v_tx_id UUID;
    v_user_split_pct NUMERIC(5,2);
    v_platform_split_pct NUMERIC(5,2);
    v_user_cashback NUMERIC(14,4);
    v_platform_revenue NUMERIC(14,4);
    v_new_pending_balance NUMERIC(14,4);
    v_idempotency_key VARCHAR(128);
BEGIN
    SELECT user_id, merchant_id INTO v_user_id, v_merchant_id
    FROM public.click_logs WHERE sub_id = p_sub_id;

    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'INVALID_SUB_ID: sub_id % does not exist', p_sub_id;
    END IF;

    SELECT user_cashback_percentage, platform_revenue_percentage
    INTO v_user_split_pct, v_platform_split_pct
    FROM public.merchants WHERE merchant_id = v_merchant_id;

    v_user_cashback := ROUND(p_gross_commission * (v_user_split_pct / 100.0), 4);
    v_platform_revenue := p_gross_commission - v_user_cashback;

    SELECT wallet_id INTO v_wallet_id
    FROM public.wallets WHERE user_id = v_user_id FOR UPDATE;

    IF v_wallet_id IS NULL THEN
        INSERT INTO public.wallets (user_id, currency) VALUES (v_user_id, p_currency)
        RETURNING wallet_id INTO v_wallet_id;
    END IF;

    INSERT INTO public.affiliate_transactions (
        sub_id, user_id, merchant_id, merchant_transaction_id,
        gross_sale_amount, gross_commission_amount, user_cashback_amount,
        platform_revenue_amount, currency, status, raw_postback_payload, processed_at
    ) VALUES (
        p_sub_id, v_user_id, v_merchant_id, p_merchant_transaction_id,
        p_gross_sale, p_gross_commission, v_user_cashback,
        v_platform_revenue, p_currency, 'PENDING', p_raw_payload, CURRENT_TIMESTAMP
    ) RETURNING transaction_id INTO v_tx_id;

    UPDATE public.wallets
    SET pending_balance = pending_balance + v_user_cashback
    WHERE wallet_id = v_wallet_id
    RETURNING pending_balance INTO v_new_pending_balance;

    v_idempotency_key := 'postback:' || v_merchant_id || ':' || p_merchant_transaction_id || ':pending';
    INSERT INTO public.wallet_ledger (
        wallet_id, transaction_id, entry_type, category, amount, balance_after, description, idempotency_key
    ) VALUES (
        v_wallet_id, v_tx_id, 'CREDIT', 'CASHBACK_PENDING', v_user_cashback, v_new_pending_balance,
        'Pending cashback from merchant sale ' || p_merchant_transaction_id, v_idempotency_key
    );

    UPDATE public.click_logs SET status = 'CONVERTED' WHERE sub_id = p_sub_id;
    RETURN v_tx_id;
END;
$$ LANGUAGE plpgsql;
