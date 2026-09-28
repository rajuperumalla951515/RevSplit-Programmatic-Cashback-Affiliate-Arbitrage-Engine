import json
from typing import Dict, Any, List
from langchain_core.tools import tool


@tool
def fetch_merchant_margin_data(merchant_slug: str) -> str:
    """
    Fetch current commission split margins, baseline rates, and active promotion paths for a merchant.
    """
    # Mock intelligent API data matching production merchants
    catalog = {
        "amazon": {
            "merchant_name": "Amazon India",
            "base_commission_rate": "8.5%",
            "user_cashback_split": "70% (5.95% effective cashback)",
            "platform_revenue_split": "30% (2.55% platform revenue)",
            "active_promotions": [
                {"category": "Electronics", "bonus_cashback": "+2.0%", "code": "ELEC2026"},
                {"category": "Fashion", "bonus_cashback": "+5.0%", "code": "STYLE50"}
            ]
        },
        "flipkart": {
            "merchant_name": "Flipkart",
            "base_commission_rate": "10.0%",
            "user_cashback_split": "70% (7.0% effective cashback)",
            "platform_revenue_split": "30% (3.0% platform revenue)",
            "active_promotions": [
                {"category": "Mobiles", "bonus_cashback": "+3.0%", "code": "MOBILEMAX"},
                {"category": "Home Appliances", "bonus_cashback": "+4.0%", "code": "HOME40"}
            ]
        }
    }
    data = catalog.get(merchant_slug.lower())
    if not data:
        return f"No active margin optimization path found for merchant '{merchant_slug}'."
    return json.dumps(data)


@tool
def evaluate_transaction_risk_rules(
    sale_amount: float,
    click_to_conversion_seconds: int,
    user_ip_country: str
) -> str:
    """
    Deterministic fraud & risk rule evaluator. Returns risk indicators, anomaly score, and safety flags.
    """
    reasons = []
    risk_score = 0.0

    # 1. Click-to-conversion velocity check (Bot detection)
    if click_to_conversion_seconds < 5:
        risk_score += 0.45
        reasons.append(f"Suspiciously fast click-to-conversion velocity ({click_to_conversion_seconds}s). Possible automated script/bot.")

    # 2. Unusually high transaction amount anomaly check
    if sale_amount > 50000:
        risk_score += 0.35
        reasons.append(f"High-value transaction amount (${sale_amount:.2f}) exceeds normal threshold ($50,000).")

    # 3. Geo-location mismatch check
    if user_ip_country.upper() not in ["IND", "USA", "CAN"]:
        risk_score += 0.20
        reasons.append(f"Transaction originated from unexpected geographic origin ({user_ip_country}).")

    result = {
        "risk_score": min(round(risk_score, 2), 1.0),
        "risk_flagged": risk_score >= 0.50,
        "reasons": reasons if reasons else ["No high-risk behaviors detected."]
    }
    return json.dumps(result)


@tool
def format_user_deal_alert(
    user_name: str,
    merchant_name: str,
    cashback_amount: float,
    currency: str,
    top_deals: List[Dict[str, Any]]
) -> str:
    """
    Generates a high-converting, personalized markdown notification payload for the user.
    """
    deals_md = "\n".join([f"- **{d.get('category', 'Deal')}**: {d.get('bonus_cashback', 'Bonus')} using code `{d.get('code', 'N/A')}`" for d in top_deals])
    
    alert = f"""### 🎉 Great News, {user_name}!
Your recent purchase at **{merchant_name}** has been tracked successfully!

- **Pending Cashback**: `{currency} {cashback_amount:.2f}` (70% commission split)
- **Status**: Verified & Pending Settlement

---
#### ⚡ Handpicked Deals Just For You:
{deals_md if top_deals else "- *Check our dashboard for daily cashback boosts!*"}

*Thank you for using RevSplit!*
"""
    return alert
