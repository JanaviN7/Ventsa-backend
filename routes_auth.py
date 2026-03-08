# routes_auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import random
import string
import smtplib
from email.message import EmailMessage
import jwt

import config
from supabase_client import supabase

router = APIRouter(prefix="/auth", tags=["Auth"])


# ================= SCHEMAS =================

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    store_name: str
    categories: list[str] | None = []


class VerifySignupRequest(BaseModel):
    email: EmailStr
    otp: str


class LoginRequest(BaseModel):
    email: EmailStr


class VerifyLoginRequest(BaseModel):
    email: EmailStr
    otp: str


# ================= HELPERS =================

def generate_otp(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def generate_store_code() -> str:
    """
    Generates a unique store code like SHOP-4821.
    Checks Supabase to ensure no collision.
    """
    for _ in range(10):  # retry up to 10 times
        digits = "".join(random.choices(string.digits, k=4))
        code = f"SHOP-{digits}"
        existing = supabase.table("stores").select("store_id").eq("store_code", code).execute()
        if not existing.data:
            return code
    # Fallback: 6-digit code
    digits = "".join(random.choices(string.digits, k=6))
    return f"SHOP-{digits}"


def send_email_otp(to_email: str, otp: str, purpose: str):
    if not config.GMAIL_USER or not config.GMAIL_APP_PASSWORD:
        print(f"[DEV OTP] {purpose.upper()} OTP for {to_email}: {otp}")
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = f"Your OTP for Smart POS ({purpose})"
        msg["From"] = config.GMAIL_USER
        msg["To"] = to_email
        msg.set_content(
            f"Your OTP is: {otp}\n"
            f"It will expire in {config.OTP_EXPIRY_MINUTES} minutes."
        )
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("⚠️ Email sending failed:", str(e))


def create_jwt(payload: dict) -> str:
    data = payload.copy()
    expiry = datetime.now(timezone.utc) + timedelta(days=config.JWT_EXPIRY_DAYS)
    data["exp"] = expiry
    return jwt.encode(data, config.JWT_SECRET, algorithm="HS256")


def validate_otp(email: str, otp: str, purpose: str):
    q = (
        supabase.table("otp_codes")
        .select("*")
        .eq("email", email)
        .eq("purpose", purpose)
        .eq("otp", str(otp))
        .eq("used", False)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not q.data:
        raise HTTPException(status_code=400, detail="OTP not found")

    row = q.data[0]

    if str(row["otp"]) != str(otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="OTP expired")

    supabase.table("otp_codes").update({"used": True}).eq("id", row["id"]).execute()
    return row


# ================= SIGNUP =================

@router.post("/signup/send-otp")
def signup_send_otp(payload: SignupRequest):
    otp = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=config.OTP_EXPIRY_MINUTES)

    supabase.table("otp_codes").insert({
        "email": payload.email,
        "otp": otp,
        "purpose": "signup",
        "expires_at": expires_at.isoformat(),
        "used": False,
        "metadata": {
            "name": payload.name,
            "store_name": payload.store_name,
            "categories": payload.categories
        }
    }).execute()

    send_email_otp(payload.email, otp, "signup")
    return {"message": "OTP sent"}


@router.post("/signup/verify")
def signup_verify(payload: VerifySignupRequest):
    otp_row = validate_otp(payload.email, payload.otp, "signup")

    # Prevent duplicate signup
    existing = (
        supabase.table("store_users")
        .select("user_id")
        .eq("email", payload.email)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=400, detail="User already exists")

    meta = otp_row.get("metadata") or {}

    # ✅ Generate unique store code
    store_code = generate_store_code()

    # Create store with store_code
    store = supabase.table("stores").insert({
        "store_name": meta.get("store_name", "Unnamed Store"),
        "categories": meta.get("categories", []),
        "store_code": store_code,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    store_id = store.data[0]["store_id"]

    # Create admin user
    user = supabase.table("store_users").insert({
        "store_id": store_id,
        "name": meta.get("name", "Admin"),
        "email": payload.email,
        "role": "admin",
        "created_at": datetime.utcnow().isoformat()
    }).execute().data[0]

    token = create_jwt({
        "user_id": user["user_id"],
        "store_id": store_id,
        "role": user["role"],
        "email": user["email"]
    })

    return {
        "token": token,
        "store_id": store_id,
        "store_code": store_code   # ✅ returned so frontend can show it
    }


# ================= LOGIN =================

@router.post("/login/send-otp")
def login_send_otp(payload: LoginRequest):
    user = (
        supabase.table("store_users")
        .select("user_id")
        .eq("email", payload.email)
        .execute()
    )
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")

    otp = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=config.OTP_EXPIRY_MINUTES)

    supabase.table("otp_codes").insert({
        "email": payload.email,
        "otp": otp,
        "purpose": "login",
        "expires_at": expires_at.isoformat(),
        "used": False
    }).execute()

    send_email_otp(payload.email, otp, "login")
    return {"message": "OTP sent"}


@router.post("/login/verify")
def login_verify(payload: VerifyLoginRequest):
    validate_otp(payload.email, payload.otp, "login")

    res = (
        supabase.table("store_users")
        .select("*")
        .eq("email", payload.email)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")

    user = res.data[0]

    # ✅ Also fetch store_code so frontend can show it in settings
    store_res = supabase.table("stores") \
        .select("store_code") \
        .eq("store_id", user["store_id"]) \
        .limit(1) \
        .execute()

    store_code = store_res.data[0]["store_code"] if store_res.data else None

    token = create_jwt({
        "user_id": user["user_id"],
        "store_id": user["store_id"],
        "role": user["role"],
        "email": user["email"]
    })

    return {
        "token": token,
        "role": user["role"],
        "store_id": user["store_id"],
        "store_code": store_code    # ✅ frontend stores this for Settings page
    }