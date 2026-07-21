"""User portal — endpoints for clients (role=user)"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, field_validator

from api.database import get_db
from api.auth import get_current_user

router = APIRouter(prefix="/portal", tags=["user-portal"])

# ── Schemas ───────────────────────────────────────────────────────────────
class BookingRequest(BaseModel):
    car_id: int
    start_date: str
    end_date: str
    full_name: str
    phone: str
    cin: str
    email: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("start_date", "end_date")
    @classmethod
    def _dates(cls, v):
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("Format YYYY-MM-DD requis")
        return v

# ── Routes ────────────────────────────────────────────────────────────────

@router.get("/cars")
def list_available_cars(
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    category:   Optional[str] = Query(None),
    brand:      Optional[str] = Query(None),
    max_rate:   Optional[float] = Query(None),
    seats:      Optional[int] = Query(None),
):
    """Catalogue public des voitures disponibles."""
    conn = get_db()
    c = conn.cursor()

    if start_date and end_date:
        c.execute("""
            SELECT * FROM cars
            WHERE status = 'available'
              AND id NOT IN (
                  SELECT car_id FROM bookings
                  WHERE status IN ('confirmed','completed')
                    AND NOT (end_date < ? OR start_date > ?)
              )
            ORDER BY daily_rate ASC
        """, (start_date, end_date))
    else:
        c.execute("SELECT * FROM cars WHERE status='available' ORDER BY daily_rate ASC")

    cars = [dict(r) for r in c.fetchall()]
    conn.close()

    if category:
        cars = [c for c in cars if c["category"].lower() == category.lower()]
    if brand:
        cars = [c for c in cars if c["brand"].lower() == brand.lower()]
    if max_rate:
        cars = [c for c in cars if c["daily_rate"] <= max_rate]
    if seats:
        cars = [c for c in cars if c["seats"] >= seats]

    return cars


@router.get("/cars/{car_id}")
def get_car_detail(car_id: int):
    """Détail d'un véhicule + créneaux réservés ce mois."""
    conn = get_db()
    car = conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
    if not car:
        conn.close()
        raise HTTPException(404, "Véhicule introuvable")

    today = date.today()
    bookings = conn.execute("""
        SELECT start_date, end_date FROM bookings
        WHERE car_id=? AND status IN ('confirmed','completed')
          AND end_date >= ?
        ORDER BY start_date
    """, (car_id, today.isoformat())).fetchall()
    conn.close()

    return {
        **dict(car),
        "upcoming_bookings": [{"start": b["start_date"], "end": b["end_date"]} for b in bookings]
    }


@router.post("/bookings", status_code=201)
def request_booking(body: BookingRequest, user=Depends(get_current_user)):
    """Client crée une demande de réservation."""
    start = date.fromisoformat(body.start_date)
    end   = date.fromisoformat(body.end_date)
    if end <= start:
        raise HTTPException(400, "La date de fin doit être après la date de début")
    days = (end - start).days

    conn = get_db()
    car = conn.execute("SELECT * FROM cars WHERE id=?", (body.car_id,)).fetchone()
    if not car:
        conn.close()
        raise HTTPException(404, "Véhicule introuvable")
    if car["status"] != "available":
        conn.close()
        raise HTTPException(409, "Véhicule non disponible")

    conflict = conn.execute("""
        SELECT id FROM bookings
        WHERE car_id=? AND status IN ('confirmed','completed')
          AND NOT (end_date < ? OR start_date > ?)
    """, (body.car_id, body.start_date, body.end_date)).fetchone()
    if conflict:
        conn.close()
        raise HTTPException(409, "Véhicule déjà réservé pour ces dates")

    total = days * car["daily_rate"]
    user_id = int(user["sub"])

    # Récupérer owner_id de la voiture pour notifier le bon admin
    owner_id = car["owner_id"] if car["owner_id"] else None

    conn.execute("""
        INSERT INTO bookings
            (car_id, client_name, client_phone, client_email, client_cin,
             start_date, end_date, total_price, status, notes, user_id, owner_id)
        VALUES (?,?,?,?,?,?,?,?,'pending',?,?,?)
    """, (body.car_id, body.full_name, body.phone, body.email, body.cin,
          body.start_date, body.end_date, total, body.notes, user_id, owner_id))
    conn.commit()
    booking_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    return {
        "id": booking_id,
        "total_price": total,
        "days": days,
        "status": "pending",
        "message": "Demande envoyée — en attente de confirmation par l'agence"
    }


@router.get("/my-bookings")
def my_bookings(user=Depends(get_current_user)):
    """Historique des réservations du client connecté."""
    user_id = int(user["sub"])
    conn = get_db()
    rows = conn.execute("""
        SELECT b.*, c.brand, c.model, c.license_plate, c.color, c.daily_rate as rate
        FROM bookings b JOIN cars c ON b.car_id = c.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.delete("/my-bookings/{booking_id}")
def cancel_my_booking(booking_id: int, user=Depends(get_current_user)):
    """Client annule une réservation en attente."""
    user_id = int(user["sub"])
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM bookings WHERE id=? AND user_id=?", (booking_id, user_id)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Réservation introuvable")
    if row["status"] not in ("pending", "confirmed"):
        conn.close()
        raise HTTPException(400, "Impossible d'annuler une réservation terminée")
    conn.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()
    return {"message": "Réservation annulée"}
