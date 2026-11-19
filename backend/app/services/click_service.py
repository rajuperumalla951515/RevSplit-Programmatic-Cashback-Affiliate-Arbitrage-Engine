import logging
import secrets
import urllib.parse
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.redis_client import store_click_session
from app.core.kafka_client import publish_event
from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MERCHANTS = {
    "amazon": {
        "merchant_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        "name": "Amazon India",
        "affiliate_template_url": "https://www.amazon.in/dp/sample?tag=revsplit-21&sub_id={sub_id}",
        "webhook_secret": "simulated_hmac_secret_revsplit",
        "user_cashback_percentage": 70.0,
        "platform_revenue_percentage": 30.0,
    },
    "flipkart": {
        "merchant_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
        "name": "Flipkart",
        "affiliate_template_url": "https://www.flipkart.com/sample?affid=revsplit&sub_id={sub_id}",
        "webhook_secret": "simulated_hmac_secret_revsplit",
        "user_cashback_percentage": 70.0,
        "platform_revenue_percentage": 30.0,
    },
    "nike": {
        "merchant_id": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
        "name": "Nike Official Store",
        "affiliate_template_url": "https://www.nike.com/in/t/sample?sub_id={sub_id}",
        "webhook_secret": "simulated_hmac_secret_revsplit",
        "user_cashback_percentage": 70.0,
        "platform_revenue_percentage": 30.0,
    },
    "apple": {
        "merchant_id": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
        "name": "Apple India",
        "affiliate_template_url": "https://www.apple.com/in/shop/sample?sub_id={sub_id}",
        "webhook_secret": "simulated_hmac_secret_revsplit",
        "user_cashback_percentage": 70.0,
        "platform_revenue_percentage": 30.0,
    },
}


def generate_sub_id() -> str:
    """Generates a cryptographically strong, unique click token (e.g. clk_7f8a9b2c3d4e5f6a)."""
    return f"clk_{secrets.token_hex(16)}"


async def create_affiliate_link(
    user_id: str,
    merchant_slug: str,
    original_url: str,
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """
    Core Step 3 Service: Accepts product URL, validates merchant, generates dynamic sub_id,
    stores token session in Redis/cache, and prepares affiliate tracking URL.
    """
    slug = merchant_slug.lower().strip()
    merchant = None

    # 1. Fetch merchant configuration from Database if active
    if db:
        try:
            query = text("SELECT merchant_id, name, affiliate_template_url FROM merchants WHERE merchant_slug = :slug AND is_active = TRUE")
            result = await db.execute(query, {"slug": slug})
            row = result.mappings().fetchone()
            if row:
                merchant = {
                    "merchant_id": str(row["merchant_id"]),
                    "name": row["name"],
                    "affiliate_template_url": row["affiliate_template_url"],
                }
        except Exception as e:
            logger.warning("Database unavailable (%s); using in-memory merchant catalog.", e)

    # Fallback to local default merchant catalog
    if not merchant:
        if slug in DEFAULT_MERCHANTS:
            merchant = DEFAULT_MERCHANTS[slug]
        else:
            # Gracefully handle dynamic merchant URLs
            merchant = {
                "merchant_id": str(secrets.token_hex(16)),
                "name": slug.title(),
                "affiliate_template_url": f"{original_url}{'&' if '?' in original_url else '?'}sub_id={{sub_id}}&aff_id=REVSPLIT",
            }

    merchant_id = str(merchant["merchant_id"])
    template_url = merchant.get("affiliate_template_url", "")

    # 2. Generate unique dynamic sub_id token
    sub_id = generate_sub_id()

    # 3. Construct dynamic affiliate redirect URL with sub_id parameter
    if "{sub_id}" in template_url:
        affiliate_redirect_url = template_url.replace("{sub_id}", sub_id)
    else:
        # Fallback query param appending to original_url
        parsed = urllib.parse.urlparse(original_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        query_params["sub_id"] = [sub_id]
        query_params["aff_id"] = ["REVSPLIT"]
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        affiliate_redirect_url = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
        )

    # 4. Cache Session Pairing in Redis / In-memory fallback
    click_session_data = {
        "sub_id": sub_id,
        "user_id": user_id,
        "merchant_id": merchant_id,
        "original_url": original_url,
        "affiliate_redirect_url": affiliate_redirect_url,
    }
    await store_click_session(sub_id, click_session_data)

    # 5. Fast DB Log Insertion (click_logs) if DB is operational
    if db:
        try:
            insert_click_log = text("""
                INSERT INTO click_logs (sub_id, user_id, merchant_id, original_url, affiliate_redirect_url, status)
                VALUES (:sub_id, :user_id, :merchant_id, :original_url, :affiliate_redirect_url, 'INITIATED')
            """)
            await db.execute(insert_click_log, {
                "sub_id": sub_id,
                "user_id": user_id,
                "merchant_id": merchant_id,
                "original_url": original_url,
                "affiliate_redirect_url": affiliate_redirect_url,
            })
            await db.commit()
        except Exception as e:
            logger.debug("Click log DB write skipped (standalone mode): %s", e)

    # 6. Non-blocking Kafka Telemetry Publication
    await publish_event(
        topic=settings.KAFKA_CLICK_TOPIC,
        key=sub_id,
        value=click_session_data
    )

    return {
        "sub_id": sub_id,
        "affiliate_url": affiliate_redirect_url,
        "redirect_gateway_url": f"/r/{sub_id}"
    }
