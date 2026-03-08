# routes_subscription.py
import hmac
import hashlib
import razorpay
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from supabase_client import supabase
from auth.dependencies import auth_required
import config

router = APIRouter(prefix="/subscription", tags=["Subscription"])

# =====================
# PLAN DEFINITIONS
# =====================

PLANS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "price_annual": 0,
        "max_products": 50,
        "max_staff": 1,
        "ledger": False,
        "reports": False,
        "invoices": False,
        "sales_history_days": 7,
    },
    "basic": {
        "name": "Basic",
        "price_monthly": 29900,   # paise (₹299)
        "price_annual": 249900,   # paise (₹2499)
        "max_products": -1,       # unlimited
        "max_staff": 5,
        "ledger": True,
        "reports": True,
        "invoices": True,
        "sales_history_days": 365,
    }
}


# =====================
# RAZORPAY CLIENT
# =====================



# =====================
# DEMO STORES
# These stores get Basic plan features permanently for free.
# =====================

DEMO_STORE_IDS = {
    "f05f3f49-750f-4908-80b9-14f363a7d27e",  # Janavi_mart SHOP-7066 — demo account
}
def get_razorpay_client():
    if not config.RAZORPAY_KEY_ID or not config.RAZORPAY_KEY_SECRET:
        raise HTTPException(500, "Razorpay not configured yet")
    return razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))


# =====================
# HELPERS
# =====================

def get_or_create_subscription(store_id: str) -> dict:
    """Get existing subscription or create a free one. Demo stores always get Basic."""
    # ✅ Demo bypass — no payment needed
    if store_id in DEMO_STORE_IDS:
        return {
            "store_id": store_id,
            "plan": "basic",
            "status": "active",
            "billing_cycle": "demo",
            "current_period_start": None,
            "current_period_end": None,
            "razorpay_subscription_id": None,
        }
    res = supabase.table("subscriptions") \
        .select("*") \
        .eq("store_id", store_id) \
        .limit(1) \
        .execute()

    if res.data:
        return res.data[0]

    # Create default free subscription
    new_sub = supabase.table("subscriptions").insert({
        "store_id": store_id,
        "plan": "free",
        "status": "active",
        "billing_cycle": None,
        "current_period_start": datetime.now(timezone.utc).isoformat(),
        "current_period_end": None,
        "razorpay_subscription_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }).execute()

    return new_sub.data[0]


def get_plan_limits(plan: str) -> dict:
    return PLANS.get(plan, PLANS["free"])


# =====================
# SCHEMAS
# =====================

class CreateOrderRequest(BaseModel):
    plan: str           # "basic"
    billing_cycle: str  # "monthly" | "annual"


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str
    billing_cycle: str


# =====================
# GET SUBSCRIPTION STATUS
# =====================

@router.get("/status")
def get_subscription_status(user=Depends(auth_required)):
    """Returns current plan, limits, and usage for this store."""
    store_id = user["store_id"]
    sub = get_or_create_subscription(store_id)
    plan = sub.get("plan", "free")
    limits = get_plan_limits(plan)

    # Get current usage
    product_count = supabase.table("products") \
        .select("product_id", count="exact") \
        .eq("store_id", store_id) \
        .execute().count or 0

    staff_count = supabase.table("store_users") \
        .select("user_id", count="exact") \
        .eq("store_id", store_id) \
        .neq("role", "admin") \
        .eq("status", "active") \
        .execute().count or 0

    return {
        "success": True,
        "subscription": {
            "plan": plan,
            "status": sub.get("status", "active"),
            "billing_cycle": sub.get("billing_cycle"),
            "current_period_end": sub.get("current_period_end"),
            "razorpay_subscription_id": sub.get("razorpay_subscription_id"),
        },
        "limits": limits,
        "usage": {
            "products": product_count,
            "staff": staff_count,
        },
        "plans": PLANS  # send all plan info for pricing page
    }


# =====================
# CREATE RAZORPAY ORDER
# =====================

@router.post("/create-order")
def create_order(payload: CreateOrderRequest, user=Depends(auth_required)):
    """Creates a Razorpay order for the selected plan + billing cycle."""
    if payload.plan not in PLANS or payload.plan == "free":
        raise HTTPException(400, "Invalid plan")
    if payload.billing_cycle not in ("monthly", "annual"):
        raise HTTPException(400, "Invalid billing cycle")

    plan = PLANS[payload.plan]
    amount = plan["price_monthly"] if payload.billing_cycle == "monthly" else plan["price_annual"]

    client = get_razorpay_client()

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "receipt": f"{user['store_id'][:8]}-{payload.plan}-{payload.billing_cycle}",
        "notes": {
            "store_id": user["store_id"],
            "plan": payload.plan,
            "billing_cycle": payload.billing_cycle
        }
    })

    return {
        "success": True,
        "order_id": order["id"],
        "amount": amount,
        "currency": "INR",
        "key_id": config.RAZORPAY_KEY_ID,
        "plan": payload.plan,
        "billing_cycle": payload.billing_cycle
    }


# =====================
# VERIFY PAYMENT + ACTIVATE
# =====================

@router.post("/verify-payment")
def verify_payment(payload: VerifyPaymentRequest, user=Depends(auth_required)):
    """Verifies Razorpay signature and activates subscription."""

    # Verify signature
    msg = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = hmac.new(
        config.RAZORPAY_KEY_SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()

    if expected != payload.razorpay_signature:
        raise HTTPException(400, "Invalid payment signature")

    # Calculate period end
    now = datetime.now(timezone.utc)
    if payload.billing_cycle == "monthly":
        period_end = now + timedelta(days=30)
    else:
        period_end = now + timedelta(days=365)

    # Update or create subscription
    existing = supabase.table("subscriptions") \
        .select("subscription_id") \
        .eq("store_id", user["store_id"]) \
        .limit(1) \
        .execute()

    sub_data = {
        "plan": payload.plan,
        "status": "active",
        "billing_cycle": payload.billing_cycle,
        "current_period_start": now.isoformat(),
        "current_period_end": period_end.isoformat(),
        "razorpay_order_id": payload.razorpay_order_id,
        "razorpay_payment_id": payload.razorpay_payment_id,
        "updated_at": now.isoformat()
    }

    if existing.data:
        supabase.table("subscriptions") \
            .update(sub_data) \
            .eq("store_id", user["store_id"]) \
            .execute()
    else:
        sub_data["store_id"] = user["store_id"]
        sub_data["created_at"] = now.isoformat()
        supabase.table("subscriptions").insert(sub_data).execute()

    return {
        "success": True,
        "message": f"Upgraded to {payload.plan.capitalize()} plan!",
        "plan": payload.plan,
        "period_end": period_end.isoformat()
    }


# =====================
# RAZORPAY WEBHOOK
# =====================

@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Handles Razorpay payment.captured and subscription.charged webhooks."""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verify webhook signature
    expected = hmac.new(
        config.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if expected != signature:
        raise HTTPException(400, "Invalid webhook signature")

    import json
    event = json.loads(body)
    event_type = event.get("event")

    if event_type == "payment.captured":
        payment = event["payload"]["payment"]["entity"]
        notes = payment.get("notes", {})
        store_id = notes.get("store_id")
        plan = notes.get("plan")
        billing_cycle = notes.get("billing_cycle")

        if store_id and plan:
            now = datetime.now(timezone.utc)
            period_end = now + timedelta(days=30 if billing_cycle == "monthly" else 365)

            supabase.table("subscriptions") \
                .update({
                    "plan": plan,
                    "status": "active",
                    "billing_cycle": billing_cycle,
                    "current_period_start": now.isoformat(),
                    "current_period_end": period_end.isoformat(),
                    "updated_at": now.isoformat()
                }) \
                .eq("store_id", store_id) \
                .execute()

    return {"status": "ok"}


# =====================
# PLAN ENFORCEMENT HELPER
# (import this in other routes to check limits)
# =====================

def check_plan_limit(store_id: str, limit_type: str):
    """
    Call this in other routes to enforce plan limits.
    limit_type: "products" | "staff" | "ledger" | "reports" | "invoices"
    Raises 403 if limit exceeded.
    """
    sub = get_or_create_subscription(store_id)
    plan = sub.get("plan", "free")
    limits = get_plan_limits(plan)

    if limit_type == "products":
        if limits["max_products"] == -1:
            return  # unlimited
        count = supabase.table("products") \
            .select("product_id", count="exact") \
            .eq("store_id", store_id) \
            .execute().count or 0
        if count >= limits["max_products"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PLAN_LIMIT_EXCEEDED",
                    "message": f"Free plan allows only {limits['max_products']} products. Upgrade to Basic for unlimited.",
                    "limit_type": "products",
                    "current": count,
                    "max": limits["max_products"]
                }
            )

    elif limit_type == "staff":
        if limits["max_staff"] == -1:
            return
        count = supabase.table("store_users") \
            .select("user_id", count="exact") \
            .eq("store_id", store_id) \
            .neq("role", "admin") \
            .eq("status", "active") \
            .execute().count or 0
        if count >= limits["max_staff"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PLAN_LIMIT_EXCEEDED",
                    "message": f"Free plan allows only {limits['max_staff']} staff. Upgrade to Basic for up to 5.",
                    "limit_type": "staff",
                    "current": count,
                    "max": limits["max_staff"]
                }
            )

    elif limit_type in ("ledger", "reports", "invoices"):
        if not limits.get(limit_type):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PLAN_LIMIT_EXCEEDED",
                    "message": f"This feature is not available on the Free plan. Upgrade to Basic.",
                    "limit_type": limit_type,
                }
            )