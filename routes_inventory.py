# routes_inventory.py
from fastapi import APIRouter, Depends, HTTPException
from supabase_client import supabase
from auth.dependencies import auth_required
from datetime import date, datetime, timezone, timedelta

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ==========================
# INVENTORY LOGS (ALL)
# ==========================
@router.get("/logs")
def get_inventory_logs(user=Depends(auth_required)):
    res = (
        supabase.table("inventory_logs")
        .select("""
            log_id,
            product_id,
            qty_changed,
            action_type,
            timestamp,
            products(name, barcode)
        """)
        .eq("store_id", user["store_id"])
        .order("timestamp", desc=True)
        .execute()
    )

    return {
        "success": True,
        "data": res.data or []
    }


# ==========================
# INVENTORY LOGS BY PRODUCT
# ==========================
@router.get("/logs/product/{product_id}")
def get_product_inventory_logs(product_id: str, user=Depends(auth_required)):
    res = (
        supabase.table("inventory_logs")
        .select("""
            log_id,
            qty_changed,
            action_type,
            timestamp
        """)
        .eq("store_id", user["store_id"])
        .eq("product_id", product_id)
        .order("timestamp", desc=True)
        .execute()
    )

    return {
        "success": True,
        "product_id": product_id,
        "logs": res.data or []
    }


# ==========================
# INVENTORY LOGS BY DATE
# ==========================
@router.get("/logs/date/{log_date}")
def get_inventory_logs_by_date(log_date: date, user=Depends(auth_required)):
    start = f"{log_date}T00:00:00"
    end = f"{log_date}T23:59:59"

    res = (
        supabase.table("inventory_logs")
        .select("""
            log_id,
            product_id,
            qty_changed,
            action_type,
            timestamp,
            products(name)
        """)
        .eq("store_id", user["store_id"])
        .gte("timestamp", start)
        .lte("timestamp", end)
        .order("timestamp", desc=True)
        .execute()
    )

    return {
        "success": True,
        "date": str(log_date),
        "logs": res.data or []
    }


# ==========================
# LOW STOCK PRODUCTS
# ==========================
@router.get("/low-stock")
def low_stock_products(user=Depends(auth_required)):
    res = (
        supabase.table("products")
        .select("product_id, name, quantity")
        .eq("store_id", user["store_id"])
        .lt("quantity", 5)
        .order("quantity")
        .execute()
    )

    return {
        "success": True,
        "data": res.data or []
    }


# ==========================
# INVENTORY ANALYTICS
# Full breakdown: stock movement, category value,
# profit per product, dead stock, top sellers
# ==========================
@router.get("/analytics")
def inventory_analytics(user=Depends(auth_required)):
    store_id = user["store_id"]

    # 1. All products with cost_price
    products_res = supabase.table("products") \
        .select("product_id, name, category, quantity, price, cost_price") \
        .eq("store_id", store_id) \
        .execute()
    products = products_res.data or []

    # Build product lookup map
    product_map = {p["product_id"]: p for p in products}

    # 2. All sale_items for this store (units sold + revenue)
    sale_items_res = supabase.table("sale_items") \
        .select("product_id, quantity, price, total") \
        .eq("store_id", store_id) \
        .execute()
    sale_items = sale_items_res.data or []

    # 3. Inventory logs — stock added (action_type = "add")
    logs_res = supabase.table("inventory_logs") \
        .select("product_id, qty_changed, action_type, timestamp") \
        .eq("store_id", store_id) \
        .execute()
    logs = logs_res.data or []

    # 4. Dead stock — products with no sales in last 30 days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    recent_sales_res = supabase.table("sale_items") \
        .select("product_id") \
        .eq("store_id", store_id) \
        .gte("created_at", cutoff) \
        .execute()
    recently_sold_ids = {s["product_id"] for s in (recent_sales_res.data or [])}

    # ---- Aggregate sale_items per product ----
    sales_map = {}  # product_id → { units_sold, revenue }
    for item in sale_items:
        pid = item["product_id"]
        if pid not in sales_map:
            sales_map[pid] = {"units_sold": 0, "revenue": 0.0}
        sales_map[pid]["units_sold"] += int(item.get("quantity", 0))
        sales_map[pid]["revenue"] += float(item.get("total", 0))

    # ---- Aggregate stock imported per product ----
    imported_map = {}  # product_id → total qty added
    for log in logs:
        if log["action_type"] == "add":
            pid = log["product_id"]
            imported_map[pid] = imported_map.get(pid, 0) + int(log.get("qty_changed", 0))

    # ---- Per product analytics ----
    product_analytics = []
    category_map = {}  # category → { stock_value, revenue, profit }

    for p in products:
        pid = p["product_id"]
        sold = sales_map.get(pid, {})
        units_sold = sold.get("units_sold", 0)
        revenue = sold.get("revenue", 0.0)
        imported = imported_map.get(pid, 0)

        selling_price = float(p.get("price", 0))
        cost_price = float(p.get("cost_price", 0))
        current_qty = int(p.get("quantity", 0))

        # Profit = (selling - cost) × units sold
        profit = (selling_price - cost_price) * units_sold if cost_price > 0 else None
        profit_margin = ((selling_price - cost_price) / selling_price * 100) if cost_price > 0 and selling_price > 0 else None

        # Stock value sitting idle
        stock_value = cost_price * current_qty if cost_price > 0 else selling_price * current_qty

        is_dead_stock = pid not in recently_sold_ids and units_sold == 0

        pa = {
            "product_id": pid,
            "name": p["name"],
            "category": p.get("category", "Uncategorized"),
            "current_qty": current_qty,
            "units_sold": units_sold,
            "total_imported": imported,
            "revenue": revenue,
            "profit": profit,
            "profit_margin": round(profit_margin, 1) if profit_margin is not None else None,
            "selling_price": selling_price,
            "cost_price": cost_price,
            "stock_value": round(stock_value, 2),
            "is_dead_stock": is_dead_stock,
        }
        product_analytics.append(pa)

        # Category rollup
        cat = p.get("category") or "Uncategorized"
        if cat not in category_map:
            category_map[cat] = {"category": cat, "stock_value": 0.0, "revenue": 0.0, "profit": 0.0, "product_count": 0}
        category_map[cat]["stock_value"] += stock_value
        category_map[cat]["revenue"] += revenue
        if profit is not None:
            category_map[cat]["profit"] += profit
        category_map[cat]["product_count"] += 1

    # ---- Top 5 best sellers by units sold ----
    top_sellers = sorted(
        [p for p in product_analytics if p["units_sold"] > 0],
        key=lambda x: x["units_sold"],
        reverse=True
    )[:5]

    # ---- Dead stock list ----
    dead_stock = [p for p in product_analytics if p["is_dead_stock"]]

    # ---- Summary ----
    total_stock_value = sum(p["stock_value"] for p in product_analytics)
    total_revenue = sum(p["revenue"] for p in product_analytics)
    total_profit = sum(p["profit"] for p in product_analytics if p["profit"] is not None)
    total_units_sold = sum(p["units_sold"] for p in product_analytics)
    total_imported = sum(p["total_imported"] for p in product_analytics)

    return {
        "success": True,
        "summary": {
            "total_products": len(products),
            "total_stock_value": round(total_stock_value, 2),
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "total_units_sold": total_units_sold,
            "total_imported": total_imported,
            "dead_stock_count": len(dead_stock),
        },
        "top_sellers": top_sellers,
        "dead_stock": dead_stock,
        "by_category": sorted(category_map.values(), key=lambda x: x["revenue"], reverse=True),
        "products": product_analytics,
    }