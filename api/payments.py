"""Payment tracking endpoints"""
from fastapi import APIRouter, HTTPException
from api.database import get_db

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/stats")
def get_payment_stats():
    """Get overall payment statistics."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT 
            COALESCE(SUM(total_price), 0) as total_revenue,
            COALESCE(SUM(deposit_paid), 0) as total_collected,
            COALESCE(SUM(balance_due), 0) as total_outstanding,
            COUNT(*) as total_bookings
        FROM bookings
        WHERE status IN ('confirmed', 'completed')
    """)
    overall = c.fetchone()

    c.execute("""
        SELECT payment_method, COUNT(*) as count, COALESCE(SUM(deposit_paid), 0) as amount
        FROM bookings
        WHERE status IN ('confirmed', 'completed') AND payment_method IS NOT NULL
        GROUP BY payment_method
    """)
    by_method = [dict(r) for r in c.fetchall()]
    conn.close()

    return {
        "total_revenue": overall["total_revenue"],
        "total_collected": overall["total_collected"],
        "total_outstanding": overall["total_outstanding"],
        "total_bookings": overall["total_bookings"],
        "by_method": by_method
    }
