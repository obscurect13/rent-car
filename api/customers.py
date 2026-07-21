"""Customer management — multi-tenant"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from api.database import get_db
from api.auth import require_admin

router = APIRouter(prefix="/customers", tags=["customers"])


def _fetch_customer(conn, owner_id: int, cin: Optional[str] = None, phone: Optional[str] = None):
    c = conn.cursor()
    if cin:
        where, param = "UPPER(b.client_cin) = UPPER(?)", cin.strip()
    else:
        where, param = "b.client_phone = ?", phone.strip()

    c.execute(f"""
        SELECT client_cin, client_name, client_phone, client_email
        FROM bookings b
        WHERE b.owner_id = ? AND {where}
        ORDER BY created_at DESC LIMIT 1
    """, (owner_id, param))
    client_info = c.fetchone()
    if not client_info:
        return None

    real_cin = client_info["client_cin"]
    c.execute("""
        SELECT b.*, c.brand, c.model, c.license_plate
        FROM bookings b JOIN cars c ON b.car_id = c.id
        WHERE b.owner_id = ? AND UPPER(b.client_cin) = UPPER(?)
        ORDER BY b.created_at DESC
    """, (owner_id, real_cin))
    bookings = [dict(r) for r in c.fetchall()]

    c.execute("""
        SELECT COALESCE(SUM(total_price),0) AS total_facture,
               COALESCE(SUM(deposit_paid),0) AS total_paye,
               COALESCE(SUM(balance_due),0)  AS total_restant,
               COUNT(*)                       AS total_bookings
        FROM bookings
        WHERE owner_id = ? AND UPPER(client_cin) = UPPER(?)
          AND status IN ('confirmed','completed')
    """, (owner_id, real_cin))
    stats = dict(c.fetchone())

    return {
        "client_cin":    real_cin,
        "client_name":   client_info["client_name"],
        "client_phone":  client_info["client_phone"],
        "client_email":  client_info["client_email"],
        "total_facture": stats["total_facture"],
        "total_paye":    stats["total_paye"],
        "total_restant": stats["total_restant"],
        "total_bookings": stats["total_bookings"],
        "bookings":      bookings,
    }


@router.get("/search")
def search_customers(query: str = Query(..., min_length=1), admin=Depends(require_admin)):
    owner_id = int(admin["sub"])
    conn = get_db()
    c = conn.cursor()
    term = f"%{query.strip()}%"
    c.execute("""
        SELECT DISTINCT client_cin, client_name, client_phone, client_email,
               COUNT(*) as booking_count
        FROM bookings
        WHERE owner_id = ?
          AND (client_name LIKE ? OR client_phone LIKE ? OR UPPER(client_cin) LIKE UPPER(?))
        GROUP BY client_cin
        ORDER BY booking_count DESC
    """, (owner_id, term, term, term))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@router.get("/{identifier}/history")
def get_customer_history(
    identifier: str,
    by: str = Query("cin"),
    admin=Depends(require_admin)
):
    owner_id = int(admin["sub"])
    conn = get_db()
    data = _fetch_customer(conn, owner_id,
                           cin=identifier if by == "cin" else None,
                           phone=identifier if by == "phone" else None)
    conn.close()
    if data is None:
        raise HTTPException(404, "Client introuvable")
    return data
