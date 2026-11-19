import json
from typing import Dict, Any, List
from langchain_core.tools import tool


@tool
def fetch_merchant_margin_data(merchant_slug: str) -> str:
    """
    Fetch current commission split margins, baseline rates, and active promotion paths for a merchant.
    """
    slug = merchant_slug.lower().strip()
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
        },
        "nike": {
            "merchant_name": "Nike Official Store",
            "base_commission_rate": "10.0%",
            "user_cashback_split": "70% (7.0% effective cashback)",
            "platform_revenue_split": "30% (3.0% platform revenue)",
            "active_promotions": [
                {"category": "Footwear", "bonus_cashback": "+3.5%", "code": "AIRMAX26"},
                {"category": "Apparel", "bonus_cashback": "+2.0%", "code": "FITRUN"}
            ]
        },
        "apple": {
            "merchant_name": "Apple India",
            "base_commission_rate": "8.5%",
            "user_cashback_split": "70% (5.95% effective cashback)",
            "platform_revenue_split": "30% (2.55% platform revenue)",
            "active_promotions": [
                {"category": "MacBook & iPad", "bonus_cashback": "+1.5%", "code": "PROAPPLE"},
                {"category": "Accessories", "bonus_cashback": "+3.0%", "code": "APPLACC"}
            ]
        }
    }
    data = catalog.get(slug)
    if not data:
        data = {
            "merchant_name": slug.title(),
            "base_commission_rate": "8.0%",
            "user_cashback_split": "70% (5.6% effective cashback)",
            "platform_revenue_split": "30% (2.4% platform revenue)",
            "active_promotions": [
                {"category": "General", "bonus_cashback": "+2.0%", "code": "DEAL2026"}
            ]
        }
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

    # Rule 1: High velocity conversion (bot / click-injection flag)
    if click_to_conversion_seconds < 10:
        risk_score += 0.55
        reasons.append("HIGH_VELOCITY_CLICK: Conversion occurred under 10 seconds (suspected bot).")

    # Rule 2: Geo IP Mismatch / Non-Domestic Traffic
    if user_ip_country != "IND":
        risk_score += 0.35
        reasons.append(f"GEO_MISMATCH: Traffic originating outside primary market ({user_ip_country}).")

    # Rule 3: High ticket value anomaly threshold
    if sale_amount > 100000.0:
        risk_score += 0.20
        reasons.append(f"HIGH_TICKET_ANOMALY: Sale amount (₹{sale_amount}) exceeds auto-clearance threshold.")

    # Rule 4: Micro-transaction rapid firing
    if sale_amount < 50.0:
        risk_score += 0.15
        reasons.append("MICRO_TX_SPAM: Micro-transaction under ₹50 detected.")

    risk_score = min(round(risk_score, 2), 1.0)
    risk_flagged = risk_score >= 0.50

    return json.dumps({
        "risk_score": risk_score,
        "risk_flagged": risk_flagged,
        "reasons": reasons
    })


@tool
def format_user_deal_alert(
    merchant_name: str,
    deals: List[Dict[str, Any]],
    user_cashback_pct: str
) -> str:
    """
    Formats a high-converting Markdown notification alert for the consumer.
    """
    if not deals:
        return f"💡 No active flash deals found for {merchant_name}, but you will still earn standard {user_cashback_pct} cashback!"

    deal_bullets = "\n".join([f"- **{d['category']}**: {d['bonus_cashback']} bonus (Code: `{d['code']}`)" for d in deals])
    return f"""### 🚀 Special Cashback Deals for {merchant_name}
You are earning **{user_cashback_pct}** of all commissions!
Active Promos:
{deal_bullets}

*Cashback automatically tracks within 10 minutes of order confirmation.*
"""
