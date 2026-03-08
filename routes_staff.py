# routes_staff.py
from fastapi import APIRouter, Depends, HTTPException, Path
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import BaseModel
from supabase_client import supabase
from auth.dependencies import auth_required
from routes_subscription import check_plan_limit  # ✅ plan enforcement
import jwt
import config

router = APIRouter(prefix="/staff", tags=["Staff"])

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def create_jwt(payload: dict) -> str:
    data = payload.copy()
    expiry = datetime.now(timezone.utc) + timedelta(days=config.JWT_EXPIRY_DAYS)
    data["exp"] = expiry
    return jwt.encode(data, config.JWT_SECRET, algorithm="HS256")


# =======================
# SCHEMAS
# =======================

class StaffCreate(BaseModel):
    name: str
    role: str       # cashier | manager
    pin: str        # 4-digit PIN


class StaffLogin(BaseModel):
    name: str
    pin_code: str
    store_code: str  # ✅ e.g. "SHOP-4821" — no UUID needed


class StaffStatusUpdate(BaseModel):
    status: str     # active | inactive


# =======================
# ADD STAFF (ADMIN ONLY)
# =======================

@router.post("/add")
def add_staff(payload: StaffCreate, user=Depends(auth_required)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin allowed")

    if payload.role not in ("cashier", "manager"):
        raise HTTPException(status_code=400, detail="Role must be cashier or manager")

    pin = payload.pin.strip()
    if len(pin) != 4 or not pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits")

    # ✅ Check free plan staff limit (1 max on free, 5 on basic)
    check_plan_limit(user["store_id"], "staff")

    staff = {
        "store_id": user["store_id"],
        "name": payload.name,
        "role": payload.role,
        "pin_hash": pwd_context.hash(pin),
        "status": "active",
        "last_activity": datetime.utcnow().isoformat()
    }

    res = supabase.table("store_users").insert(staff).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to add staff")

    return {"success": True, "staff": res.data[0]}


# =======================
# LIST STAFF (ADMIN ONLY)
# =======================

@router.get("")
def list_staff(user=Depends(auth_required)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin allowed")

    res = (
        supabase
        .table("store_users")
        .select("user_id,name,role,status,last_activity,created_at")
        .eq("store_id", user["store_id"])
        .neq("role", "admin")
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "success": True,
        "count": len(res.data or []),
        "staff": res.data or []
    }


# =======================
# ACTIVATE / DEACTIVATE STAFF
# =======================

@router.patch("/{staff_id}/status")
def update_staff_status(
    staff_id: str = Path(...),
    payload: StaffStatusUpdate = None,
    user=Depends(auth_required)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin allowed")

    if not payload or payload.status not in ("active", "inactive"):
        raise HTTPException(status_code=400, detail="Status must be active or inactive")

    res = (
        supabase
        .table("store_users")
        .update({"status": payload.status})
        .eq("user_id", staff_id)
        .eq("store_id", user["store_id"])
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Staff not found")

    return {"success": True, "staff": res.data[0]}


# =======================
# STAFF LOGIN (PIN + STORE CODE)
# =======================

@router.post("/login")
def staff_login(payload: StaffLogin):
    # ✅ Look up store by store_code — staff never needs to know UUID
    store_res = supabase.table("stores") \
        .select("store_id") \
        .eq("store_code", payload.store_code.upper().strip()) \
        .limit(1) \
        .execute()

    if not store_res.data:
        raise HTTPException(status_code=401, detail="Invalid store code")

    store_id = store_res.data[0]["store_id"]

    # Find active staff by name within that store
    res = (
        supabase
        .table("store_users")
        .select("*")
        .eq("name", payload.name)
        .eq("store_id", store_id)
        .eq("status", "active")
        .limit(1)
        .execute()
    )

    staff = res.data[0] if res.data else None
    if not staff:
        raise HTTPException(401, "Invalid name, store code, or PIN")

    if not pwd_context.verify(payload.pin_code, staff["pin_hash"]):
        raise HTTPException(401, "Invalid name, store code, or PIN")

    # Update last activity
    supabase.table("store_users").update({
        "last_activity": datetime.utcnow().isoformat()
    }).eq("user_id", staff["user_id"]).execute()

    # ✅ Generate JWT so staff can make authenticated API calls
    token = create_jwt({
        "user_id": staff["user_id"],
        "store_id": staff["store_id"],
        "role": staff["role"],
        "email": staff.get("email", "")
    })

    return {
        "success": True,
        "token": token,
        "staff": {
            "user_id": staff["user_id"],
            "name": staff["name"],
            "role": staff["role"],
            "store_id": staff["store_id"]
        }
    }