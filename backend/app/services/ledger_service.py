import json
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def settle_commission_postback(
    sub_id: str,
    merchant_transaction_id: str,
    gross_sale_amount: float,
    gross_commission_amount: float,
    currency: str,
    raw_payload: Dict[str, Any],
    db: AsyncSession
) -> str:
    """
    Core Step 4 Financial Settlement Engine:
    Executes PostgreSQL stored procedure `process_commission_postback` which:
    1. Resolves sub_id to user_id and merchant_id
    2. Calculates margin split (e.g. 70% user / 30% platform)
    3. Acquires a pessimistic row-level lock (`SELECT FOR UPDATE`) on target user wallet
    4. Enforces idempotency via composite unique key `(merchant_id, merchant_transaction_id)`
    5. Writes entry to double-entry wallet ledger and updates pending balance atomically.
    """
    query = text("""
        SELECT process_commission_postback(
            :sub_id,
            :merchant_tx_id,
            :gross_sale,
            :gross_commission,
            :currency,
            :raw_payload
        ) AS transaction_id;
    """)

    try:
        result = await db.execute(query, {
            "sub_id": sub_id,
            "merchant_tx_id": merchant_transaction_id,
            "gross_sale": gross_sale_amount,
            "gross_commission": gross_commission_amount,
            "currency": currency,
            "raw_payload": json.dumps(raw_payload)
        })
        await db.commit()
        tx_id = result.scalar()
        logger.info(f"Commission settled successfully. Transaction ID: {tx_id}")
        return str(tx_id)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to settle commission postback for sub_id={sub_id}, merchant_tx={merchant_transaction_id}: {e}")
        raise e
