import os
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from app.db.database import get_conn, row_to_dict
from app.services.security import decode_token
from app.services.plans import PLANS, normalize_plan

router = APIRouter(prefix="/api", tags=["payments"])


def current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    payload = decode_token(authorization.replace("Bearer ", ""))
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"id": int(payload["sub"]), "email": payload["email"]}

class CheckoutRequest(BaseModel):
    plan: str = "premium"
    provider: str = "razorpay"

class ManualPaymentRequest(BaseModel):
    plan: str = "premium"
    payment_reference: str
    provider: str = "razorpay"

@router.get("/plans")
def list_plans():
    return {"plans": PLANS}

@router.post("/payments/checkout")
def create_checkout(data: CheckoutRequest, user=Depends(current_user)):
    plan = normalize_plan(data.plan)
    if plan == "free":
        raise HTTPException(status_code=400, detail="Free plan does not need payment")

    provider = data.provider.lower().strip()
    if provider == "razorpay":
        base_link = os.getenv("RAZORPAY_PAYMENT_LINK", "").strip()
        if not base_link:
            return {
                "provider": "razorpay",
                "plan": plan,
                "checkout_url": None,
                "message": "Add RAZORPAY_PAYMENT_LINK in backend environment to enable real Razorpay checkout.",
            }
        separator = "&" if "?" in base_link else "?"
        checkout_url = f"{base_link}{separator}plan={plan}&user_id={user['id']}"
        return {"provider": "razorpay", "plan": plan, "checkout_url": checkout_url}

    if provider == "stripe":
        checkout_url = os.getenv("STRIPE_CHECKOUT_URL", "").strip()
        if not checkout_url:
            return {
                "provider": "stripe",
                "plan": plan,
                "checkout_url": None,
                "message": "Add STRIPE_CHECKOUT_URL or implement Stripe Checkout Session API.",
            }
        return {"provider": "stripe", "plan": plan, "checkout_url": checkout_url}

    raise HTTPException(status_code=400, detail="Use provider razorpay or stripe")

@router.post("/payments/manual-confirm")
def manual_confirm_payment(data: ManualPaymentRequest, user=Depends(current_user)):
    """Admin-lite paid beta helper: after checking Razorpay dashboard manually, save reference and activate plan."""
    plan = normalize_plan(data.plan)
    if plan == "free":
        raise HTTPException(status_code=400, detail="Choose premium or team")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO payment_records(user_id,provider,plan,amount_inr,payment_reference,status)
                VALUES(%s,%s,%s,%s,%s,%s) RETURNING id
            """, (user["id"], data.provider, plan, 0, data.payment_reference, "pending_admin_verification"))
            pid = cur.fetchone()["id"]
    return {"id": pid, "message": "Payment reference saved. Verify in Razorpay, then activate user plan from admin/database."}

@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request):
    """Production hook placeholder. Add signature verification before auto-activating plans."""
    payload = await request.json()
    return {"received": True, "message": "Razorpay webhook received. Add signature verification before production activation.", "event": payload.get("event")}
