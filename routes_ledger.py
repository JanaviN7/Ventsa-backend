# routes_ledger.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase_client import supabase
from auth.dependencies import auth_required
from datetime import datetime, timedelta, timezone
from typing import Optional

router = APIRouter(prefix="/ledger", tags=["Ledger"])


# =====================
# SCHEMAS
# =====================

class AddCustomer(BaseModel):
    name: str
    phone: Optional[str] = None


class LedgerEntry(BaseModel):
    customer_name: str
    phone: Optional[str] = None
    amount: float
    type: str                       # DEBIT | CREDIT
    note: Optional[str] = None
    due_date: Optional[str] = None  # ISO date string, only for DEBIT entries


# =====================
# HELPERS
# =====================

def _get_or_create_customer(store_id: str, name: str, phone: Optional[str]):
    q = supabase.table("customers").select("*") \
        .eq("store_id", store_id) \
        .ilike("name", name)

    if phone:
        q = q.eq("phone", phone)

    res = q.limit(1).execute()

    if res.data:
        return res.data[0]

    created = supabase.table("customers").insert({
        "store_id": store_id,
        "name": name,
        "phone": phone,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return created.data[0]


def _compute_status(balance: float, entries: list) -> str:
    """
    Cleared  → balance == 0
    Overdue  → balance > 0 AND any debit entry past its due_date
    Due      → balance > 0 but no overdue entries
    """
    if balance <= 0:
        return "CLEARED"

    now = datetime.now(timezone.utc)
    for e in entries:
        if e.get("type") == "DEBIT" and e.get("due_date"):
            due = datetime.fromisoformat(e["due_date"].replace("Z", "+00:00"))
            if now > due:
                return "OVERDUE"

    return "DUE"


def _build_statement(entries: list) -> list:
    """
    Takes raw ledger rows ordered by created_at and returns
    each row with a running_balance field.
    """
    running = 0.0
    statement = []
    for e in entries:
        if e["type"] == "DEBIT":
            running += e["amount"]
        else:
            running -= e["amount"]
        statement.append({
            **e,
            "running_balance": round(running, 2)
        })
    return statement


# =====================
# ADD CUSTOMER
# =====================

@router.post("/customer/add")
def add_customer(payload: AddCustomer, user=Depends(auth_required)):
    customer = _get_or_create_customer(
        user["store_id"], payload.name, payload.phone
    )
    return {"success": True, "customer": customer}


# =====================
# LIST ALL CUSTOMERS
# =====================

@router.get("/customers")
def list_customers(user=Depends(auth_required)):
    """
    Returns all customers for this store with:
    - current balance
    - last transaction date
    - status (CLEARED / DUE / OVERDUE)
    """
    customers = supabase.table("customers") \
        .select("customer_id,name,phone,created_at") \
        .eq("store_id", user["store_id"]) \
        .order("created_at", desc=True) \
        .execute().data or []

    if not customers:
        return {"success": True, "data": []}

    customer_ids = [c["customer_id"] for c in customers]

    # One query for all ledger entries
    ledger_rows = supabase.table("customer_ledger") \
        .select("customer_id,amount,type,due_date,created_at") \
        .eq("store_id", user["store_id"]) \
        .in_("customer_id", customer_ids) \
        .order("created_at") \
        .execute().data or []

    # Group entries by customer
    entries_map: dict = {c["customer_id"]: [] for c in customers}
    for r in ledger_rows:
        entries_map[r["customer_id"]].append(r)

    result = []
    for c in customers:
        cid = c["customer_id"]
        entries = entries_map[cid]

        balance = 0.0
        last_txn_date = None
        for e in entries:
            balance += e["amount"] if e["type"] == "DEBIT" else -e["amount"]
            last_txn_date = e["created_at"]  # already ordered asc, last wins

        status = _compute_status(balance, entries)

        result.append({
            "customer_id": cid,
            "name": c["name"],
            "phone": c["phone"],
            "member_since": c["created_at"],
            "balance": round(balance, 2),
            "last_transaction": last_txn_date,
            "status": status          # CLEARED | DUE | OVERDUE
        })

    return {"success": True, "data": result}


# =====================
# ADD LEDGER ENTRY
# =====================

@router.post("/entry/add")
def add_ledger_entry(payload: LedgerEntry, user=Depends(auth_required)):
    if payload.type not in ("DEBIT", "CREDIT"):
        raise HTTPException(400, "Type must be DEBIT or CREDIT")

    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be greater than 0")

    customer = _get_or_create_customer(
        user["store_id"], payload.customer_name, payload.phone
    )

    # For DEBIT: default due_date = 30 days from today if not provided
    due_date = None
    if payload.type == "DEBIT":
        if payload.due_date:
            due_date = payload.due_date
        else:
            due_date = (datetime.utcnow() + timedelta(days=30)).isoformat()

    res = supabase.table("customer_ledger").insert({
        "store_id": user["store_id"],
        "customer_id": customer["customer_id"],
        "amount": payload.amount,
        "type": payload.type,
        "note": payload.note,
        "due_date": due_date,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return {
        "success": True,
        "entry": res.data[0],
        "customer": {
            "customer_id": customer["customer_id"],
            "name": customer["name"],
            "phone": customer["phone"]
        }
    }


# =====================
# CUSTOMER STATEMENT
# (full transaction history with running balance)
# =====================

@router.get("/customer/{customer_id}/statement")
def get_customer_statement(customer_id: str, user=Depends(auth_required)):
    """
    Returns full transaction statement for one customer with:
    - Each entry + running_balance
    - Summary: total_debit, total_credit, current_balance, status
    - Customer info: name, phone, member_since, last_payment
    """
    # Get customer info
    customer_res = supabase.table("customers") \
        .select("*") \
        .eq("store_id", user["store_id"]) \
        .eq("customer_id", customer_id) \
        .limit(1) \
        .execute()

    if not customer_res.data:
        raise HTTPException(404, "Customer not found")

    customer = customer_res.data[0]

    # Get all entries ordered by date
    entries = supabase.table("customer_ledger") \
        .select("*") \
        .eq("store_id", user["store_id"]) \
        .eq("customer_id", customer_id) \
        .order("created_at") \
        .execute().data or []

    # Build statement with running balance
    statement = _build_statement(entries)

    # Summary calculations
    total_debit = sum(e["amount"] for e in entries if e["type"] == "DEBIT")
    total_credit = sum(e["amount"] for e in entries if e["type"] == "CREDIT")
    current_balance = round(total_debit - total_credit, 2)
    status = _compute_status(current_balance, entries)

    last_payment = None
    for e in reversed(entries):
        if e["type"] == "CREDIT":
            last_payment = e["created_at"]
            break

    return {
        "success": True,
        "customer": {
            "customer_id": customer["customer_id"],
            "name": customer["name"],
            "phone": customer["phone"],
            "member_since": customer["created_at"]
        },
        "summary": {
            "total_debit": round(total_debit, 2),
            "total_credit": round(total_credit, 2),
            "current_balance": current_balance,
            "status": status,
            "last_payment": last_payment,
            "total_transactions": len(entries)
        },
        "statement": statement
    }


# =====================
# CUSTOMER BALANCE (quick)
# =====================

@router.get("/customer/{customer_id}/balance")
def customer_balance(customer_id: str, user=Depends(auth_required)):
    rows = supabase.table("customer_ledger") \
        .select("amount,type,due_date") \
        .eq("store_id", user["store_id"]) \
        .eq("customer_id", customer_id) \
        .execute().data or []

    balance = 0.0
    for r in rows:
        balance += r["amount"] if r["type"] == "DEBIT" else -r["amount"]

    status = _compute_status(balance, rows)

    return {
        "success": True,
        "balance": round(balance, 2),
        "status": status
    }


# =====================
# CUSTOMERS WITH DUES
# =====================

@router.get("/dues")
def customers_with_dues(user=Depends(auth_required)):
    customers = supabase.table("customers") \
        .select("customer_id,name,phone") \
        .eq("store_id", user["store_id"]) \
        .execute().data or []

    if not customers:
        return {"success": True, "data": []}

    customer_ids = [c["customer_id"] for c in customers]

    ledger_rows = supabase.table("customer_ledger") \
        .select("customer_id,amount,type,due_date,created_at") \
        .eq("store_id", user["store_id"]) \
        .in_("customer_id", customer_ids) \
        .execute().data or []

    # Group by customer
    entries_map: dict = {c["customer_id"]: [] for c in customers}
    for r in ledger_rows:
        entries_map[r["customer_id"]].append(r)

    customer_map = {c["customer_id"]: c for c in customers}

    result = []
    for cid, entries in entries_map.items():
        balance = sum(
            e["amount"] if e["type"] == "DEBIT" else -e["amount"]
            for e in entries
        )
        if balance > 0:
            status = _compute_status(balance, entries)
            last_txn = max((e["created_at"] for e in entries), default=None)
            c = customer_map[cid]
            result.append({
                "customer_id": cid,
                "name": c["name"],
                "phone": c["phone"],
                "due_amount": round(balance, 2),
                "status": status,
                "last_transaction": last_txn
            })

    result.sort(key=lambda x: x["due_amount"], reverse=True)

    return {"success": True, "data": result}