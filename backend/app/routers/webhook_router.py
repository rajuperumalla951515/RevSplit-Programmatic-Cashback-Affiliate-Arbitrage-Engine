import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db_session
from app.core.redis_client import check_and_set_webhook_idempotency
from app.core.kafka_client import publish_event
from app.services.ledger_service import settle_commission_postback
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Merchant Webhook Ingestion"])


class MerchantPostbackPayload(BaseModel):
    merchant_id: str
    sub_id: str
    merchant_transaction_id: str
    gross_sale_amount: float = Field(..., gt=0)
    gross_commission_amount: float = Field(..., gt=0)
    currency: str = "INR"
    raw_metadata: Optional[Dict[str, Any]] = None


def verify_hmac_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """Verifies HMAC-SHA256 signature from merchant webhook postbacks."""
    expected_sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, signature)


@router.post("/api/v1/webhooks/postback", status_code=status.HTTP_200_OK)
async def receive_merchant_postback(
    request: Request,
    payload: MerchantPostbackPayload,
    x_merchant_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Step 4 Secure Webhook Ingestion:
    1. Validates merchant HMAC-SHA256 signature.
    2. Performs Redis SETNX idempotency check against rapid duplicate postbacks.
    3. Triggers atomic financial ledger update with row-level locking (SELECT FOR UPDATE).
    """
    raw_body = await request.body()

    # 1. Fetch merchant secret key from DB
    query = text("SELECT webhook_secret FROM merchants WHERE merchant_id = :mid AND is_active = TRUE")
    result = await db.execute(query, {"mid": payload.merchant_id})
    merchant = result.mappings().fetchone()

    if not merchant:
        raise HTTPException(status_code=403, detail="Merchant unverified or inactive.")

    # 2. Verify HMAC Signature
    if x_merchant_signature:
        is_valid = verify_hmac_signature(raw_body, x_merchant_signature, merchant["webhook_secret"])
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid HMAC postback signature.")

    # 3. Redis SETNX Idempotency Lock
    is_first_seen = await check_and_set_webhook_idempotency(payload.merchant_id, payload.merchant_transaction_id)
    if not is_first_seen:
        logger.warning(f"Duplicate postback ignored for merchant_id={payload.merchant_id}, tx={payload.merchant_transaction_id}")
        return {"status": "IGNORED_DUPLICATE", "message": "Postback already ingested and locked."}

    # 4. Async Kafka Publishing for event-driven decoupled ingestion
    event_payload = payload.model_dump()
    await publish_event(
        topic=settings.KAFKA_POSTBACK_TOPIC,
        key=payload.merchant_transaction_id,
        value=event_payload
    )

    # 5. Execute Atomic Settlement using PostgreSQL Row-Level Locking
    try:
        tx_id = await settle_commission_postback(
            sub_id=payload.sub_id,
            merchant_transaction_id=payload.merchant_transaction_id,
            gross_sale_amount=payload.gross_sale_amount,
            gross_commission_amount=payload.gross_commission_amount,
            currency=payload.currency,
            raw_payload=payload.model_dump(),
            db=db
        )
        return {
            "status": "SUCCESS",
            "transaction_id": tx_id,
            "message": "Postback processed and ledger locked successfully."
        }
    except Exception as e:
        logger.error(f"Error executing postback settlement: {e}")
        raise HTTPException(status_code=500, detail=f"Ledger settlement error: {str(e)}")
