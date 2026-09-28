# RevSplit: Programmatic Cashback & Affiliate Arbitrage Engine
## System Architecture & Technical Specification

RevSplit is a high-throughput, low-latency affiliate link monetization and programmatic cashback arbitrage engine. It intercepts e-commerce outbound traffic, dynamically injects tracking telemetry (`sub_id`), processes real-time postback webhooks from affiliate networks, and programmatically distributes commission margins (e.g., 70% user cashback / 30% platform revenue) using a double-entry financial ledger.

---

## 1. High-Level Architecture Diagram

```
                                 [ USER / CLIENT ]
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │                                           │
         1. Dynamic Link / Outbound                     4. Webhook Postback
                   │                                           │
                   ▼                                           ▼
      ┌─────────────────────────┐                 ┌─────────────────────────┐
      │  FastAPI Redirect Core  │                 │  Node.js Webhook Core   │
      │  (Low-Latency Gateway)  │                 │  (Ingestion & Sig Check)│
      └────────────┬────────────┘                 └────────────┬────────────┘
                   │                                           │
         ┌─────────┴─────────┐                       ┌─────────┴─────────┐
         │                   │                       │                   │
         ▼                   ▼                       ▼                   ▼
  ┌─────────────┐     ┌─────────────┐         ┌─────────────┐     ┌─────────────┐
  │ Redis Cache │     │ Kafka Topic │         │ Redis Cache │     │ Kafka Topic │
  │ (Token/Rate)│     │`click.events│         │ (Idempotency│     │`postbacks`  │
  └─────────────┘     └──────┬──────┘         └─────────────┘     └──────┬──────┘
                             │                                           │
                             ▼                                           ▼
                      ┌─────────────┐                             ┌─────────────┐
                      │    Kafka    │                             │    Kafka    │
                      │   Consumer  │                             │   Consumer  │
                      └──────┬──────┘                             └──────┬──────┘
                             │                                           │
                             ▼                                           ▼
                   ┌───────────────────────────────────────────────────────────┐
                   │               PostgreSQL Database Cluster                │
                   │  - ACID Double-Entry Financial Ledger                    │
                   │  - Row-Level Locking (`SELECT ... FOR UPDATE`)           │
                   │  - Idempotent Transaction State Machine                  │
                   └───────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Data Flow

### A. Click Tracking & Dynamic Outbound Link Generation Pipeline (Sub-10ms Target)
1. **User Request**: A user clicks a product link or submits a merchant URL (e.g., `https://merchant.com/product/123`).
2. **Token Generation & Session Pairing**: 
   - FastAPI generates a cryptographically unique, high-entropy `sub_id` (e.g., `clk_9f8d7c6b5a4e3d2c`).
   - FastAPI writes `sub_id -> { user_id, merchant_id, original_url, timestamp }` into **Redis** with a short TTL (e.g., 24 hours).
3. **Async Event Telemetry**: 
   - Click metadata is published to the `click.events` Kafka topic asynchronously (non-blocking).
4. **Instant 302 Redirect**: 
   - The user is immediately redirected to the merchant with appended affiliate query parameters (e.g., `https://merchant.com/product/123?aff_id=REVSPLIT&sub_id=clk_9f8d7c6b5a4e3d2c`).

### B. Merchant Commission Postback & Webhook Ingestion Pipeline
1. **Merchant Webhook**: Merchant affiliate network sends a POST back to `/api/v1/webhooks/postback` containing `sub_id`, `transaction_id`, `sale_amount`, `commission_amount`, and `signature`.
2. **Signature Verification & Deduplication**:
   - Signature (HMAC-SHA256) is calculated and verified.
   - Redis checks `SETNX webhook_idempotency:{merchant_id}:{transaction_id}`. If key exists, request is immediately acknowledged (HTTP 200) without reprocessing.
3. **Event Queue**: Valid postback payload is published to `postback.confirmed` topic in Kafka.

### C. Financial Settlement & Double-Entry Ledger Pipeline
1. **Kafka Settlement Consumer**: Consumes `postback.confirmed` payload.
2. **ACID Transaction Execution**:
   - Opens a PostgreSQL transaction (`BEGIN`).
   - Acquires a row-level lock (`SELECT * FROM wallets WHERE user_id = $1 FOR UPDATE`).
   - Validates transaction state (`PENDING` -> `VERIFIED` -> `PAIDOUT`).
   - Programmatically calculates margin split:
     $$\text{Cashback}_{\text{user}} = \text{Commission} \times 0.70$$
     $$\text{Revenue}_{\text{platform}} = \text{Commission} \times 0.30$$
   - Inserts immutable debit/credit rows into `wallet_ledger`.
   - Updates `wallets` table pending and available balances.
   - Updates `affiliate_transactions` state to `VERIFIED`.
   - Commits transaction (`COMMIT`).

---

## 3. Financial Ledger Integrity & Security Guarantees

1. **Double-Entry Accounting System**: Balances are derived from immutable journal entries. Credits and debits must sum to zero across system accounts.
2. **Strict Concurrency Control**: All financial writes acquire pessimistic locks via `FOR UPDATE` to guarantee serializable isolation during concurrent webhook deliveries.
3. **Idempotency Keys**: Network retries and duplicate postbacks are neutralized via composite unique constraints (`merchant_id` + `merchant_transaction_id`).
