"""Dashboard statistics endpoint — multi-tenant"""
from fastapi import APIRouter, Depends
from datetime import date
from api.database import get_db
from api.auth import require_admin

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def get_stats(admin=Depends(require_admin)):
    owner_id = int(admin["sub"])
    conn = get_db()
    c = conn.cursor()

    def q(sql, params=None):
        c.execute(sql, params or [])
        return c.fetchone()

    o = owner_id
    total_cars         = q("SELECT COUNT(*) as v FROM cars WHERE owner_id=?", [o])["v"]
    available          = q("SELECT COUNT(*) as v FROM cars WHERE owner_id=? AND status='available'", [o])["v"]
    maintenance        = q("SELECT COUNT(*) as v FROM cars WHERE owner_id=? AND status='maintenance'", [o])["v"]
    active_bookings    = q("SELECT COUNT(*) as v FROM bookings WHERE owner_id=? AND status='confirmed'", [o])["v"]
    completed_bookings = q("SELECT COUNT(*) as v FROM bookings WHERE owner_id=? AND status='completed'", [o])["v"]
    rev_confirmed      = q("SELECT COALESCE(SUM(total_price),0) as v FROM bookings WHERE owner_id=? AND status='confirmed'", [o])["v"]
    rev_completed      = q("SELECT COALESCE(SUM(total_price),0) as v FROM bookings WHERE owner_id=? AND status='completed'", [o])["v"]

    today = date.today().isoformat()
    overdue = q("SELECT COUNT(*) as v FROM bookings WHERE owner_id=? AND status='confirmed' AND end_date<?", [o, today])["v"]

    ps = q("""
        SELECT COALESCE(SUM(total_price),0) as total_revenue,
               COALESCE(SUM(deposit_paid),0) as total_collected,
               COALESCE(SUM(balance_due),0) as total_outstanding,
               COALESCE(SUM(deposit_amount),0) as total_deposits_requested
        FROM bookings WHERE owner_id=? AND status IN ('confirmed','completed')
    """, [o])

    c.execute("""
        SELECT payment_method, COUNT(*) as count, COALESCE(SUM(deposit_paid),0) as amount
        FROM bookings WHERE owner_id=? AND status IN ('confirmed','completed') AND payment_method IS NOT NULL
        GROUP BY payment_method
    """, [o])
    payment_methods = [dict(r) for r in c.fetchall()]

    c.execute("""
        SELECT COUNT(*) as v FROM inspections i
        JOIN bookings b ON i.booking_id = b.id WHERE b.owner_id=?
    """, [o])
    total_inspections = c.fetchone()["v"]

    c.execute("""
        SELECT COALESCE(SUM(i.damage_cost),0) as v FROM inspections i
        JOIN bookings b ON i.booking_id = b.id WHERE b.owner_id=?
    """, [o])
    total_damage = c.fetchone()["v"]

    c.execute("SELECT COUNT(*) as v FROM insurance_tracking WHERE owner_id=? AND status='active'", [o])
    total_insurance = c.fetchone()["v"]

    conn.close()
    return {
        "total_cars": total_cars,
        "available_cars": available,
        "maintenance_cars": maintenance,
        "active_bookings": active_bookings,
        "completed_bookings": completed_bookings,
        "overdue_bookings": overdue,
        "total_revenue": rev_confirmed + rev_completed,
        "total_collected": ps["total_collected"],
        "total_outstanding": ps["total_outstanding"],
        "total_deposits_requested": ps["total_deposits_requested"],
        "payment_methods": payment_methods,
        "total_inspections": total_inspections,
        "total_damage_cost": total_damage,
        "total_insurance_records": total_insurance,
    }
