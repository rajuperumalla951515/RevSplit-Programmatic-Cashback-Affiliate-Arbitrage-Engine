from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.services.click_service import create_affiliate_link
from app.redis_client import get_click_session

router = APIRouter(tags=["Click Tracking & Link Routing"])


class LinkGenerationRequest(BaseModel):
    user_id: str
    merchant_slug: str
    original_url: HttpUrl


class LinkGenerationResponse(BaseModel):
    sub_id: str
    affiliate_url: str
    redirect_gateway_url: str


@router.post("/api/v1/links/generate", response_model=LinkGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_monetized_link(
    request: LinkGenerationRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Step 3 Endpoint: Accepts product link, tokenizes sub_id, stores session in Redis,
    and publishes telemetry event to Kafka.
    """
    try:
        result = await create_affiliate_link(
            user_id=request.user_id,
            merchant_slug=request.merchant_slug,
            original_url=str(request.original_url),
            db=db
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal link generation error: {str(e)}")


@router.get("/r/{sub_id}", response_class=RedirectResponse)
async def perform_click_redirect(sub_id: str, request: Request):
    """
    Step 3 Sub-10ms Outbound Gateway: Fetches dynamic URL from Redis cache
    and issues an immediate HTTP 302 redirect.
    """
    session_data = await get_click_session(sub_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Click token expired or invalid.")

    redirect_url = session_data.get("affiliate_redirect_url")
    if not redirect_url:
        raise HTTPException(status_code=400, detail="Invalid target redirect URL.")

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
