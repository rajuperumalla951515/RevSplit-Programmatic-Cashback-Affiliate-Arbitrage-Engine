import secrets
import urllib.parse
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.redis_client import store_click_session
from app.core.kafka_client import publish_event
from app.core.config import settings


def generate_sub_id() -> str:
    """Generates a cryptographically strong, unique click token (e.g. clk_7f8a9b2c3d4e5f6a)."""
    return f"clk_{secrets.token_hex(16)}"


async def create_affiliate_link(
    user_id: str,
    merchant_slug: str,
    original_url: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Core Step 3 Service: Accepts product URL, validates merchant, generates dynamic sub_id,
    stores token session in Redis, and prepares affiliate tracking URL.
    """
    # 1. Fetch merchant configuration from Database
    query = text("SELECT merchant_id, name, affiliate_template_url FROM merchants WHERE merchant_slug = :slug AND is_active = TRUE")
    result = await db.execute(query, {"slug": merchant_slug})
    merchant = result.mappings().fetchone()

    if not merchant:
        raise ValueError(f"Active merchant with slug '{merchant_slug}' not found.")

    merchant_id = str(merchant["merchant_id"])
    template_url = merchant["affiliate_template_url"]

    # 2. Generate unique dynamic sub_id token
    sub_id = generate_sub_id()

    # 3. Construct dynamic affiliate redirect URL with sub_id parameter
    # Example template: https://merchant.com/p/{product_id}?aff_id=REVSPLIT&sub_id={sub_id}
    if "{sub_id}" in template_url:
        affiliate_redirect_url = template_url.replace("{sub_id}", sub_id)
    else:
        # Fallback query param appending
        parsed = urllib.parse.urlparse(original_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        query_params["sub_id"] = [sub_id]
        query_params["aff_id"] = ["REVSPLIT"]
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        affiliate_redirect_url = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
        )

    # 4. Cache Session Pairing in Redis (sub_id -> metadata)
    click_session_data = {
        "sub_id": sub_id,
        "user_id": user_id,
        "merchant_id": merchant_id,
        "original_url": original_url,
        "affiliate_redirect_url": affiliate_redirect_url,
    }
    await store_click_session(sub_id, click_session_data)

    # 5. Fast DB Log Insertion (click_logs)
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
