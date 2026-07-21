"""Booking management endpoints — multi-tenant"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import sqlite3
from datetime import date
from api.database import get_db
from api.models import BookingCreate, BookingUpdate, PaymentUpdate
from api.auth import require_admin

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _owner(admin) -> int:
    return int(admin["sub"])


@router.get("")
def list_bookings(
    status: Optional[str] = None,
    client_search: Optional[str] = None,
    admin=Depends(require_admin)
):
    owner_id = _owner(admin)
    conn = get_db()
    c = conn.cursor()
    query = """
        SELECT b.*, c.brand, c.model, c.license_plate
        FROM bookings b JOIN cars c ON b.car_id = c.id
        WHERE b.owner_id = ?
    """
    params = [owner_id]
    if status:
        query += " AND b.status = ?"
        params.append(status)
    if client_search:
        t = f"%{client_search}%"
        query += " AND (b.client_name LIKE ? OR b.client_phone LIKE ? OR b.client_cin LIKE ?)"
        params.extend([t, t, t])
    query += " ORDER BY b.created_at DESC"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@router.get("/overdue")
def get_overdue_bookings(admin=Depends(require_admin)):
    owner_id = _owner(admin)
    today = date.today().isoformat()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT b.*, c.brand, c.model, c.license_plate,
               CAST(julianday(?) - julianday(b.end_date) AS INTEGER) as days_overdue
        FROM bookings b JOIN cars c ON b.car_id = c.id
        WHERE b.owner_id = ? AND b.status = 'confirmed' AND b.end_date < ?
        ORDER BY b.end_date ASC
    """, (today, owner_id, today))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@router.post("", status_code=201)
def create_booking(data: dict, admin=Depends(require_admin)):
    owner_id = _owner(admin)
    required = ["car_id", "client_name", "client_phone", "client_cin", "start_date", "end_date"]
    for field in required:
        if field not in data or data[field] is None:
            raise HTTPException(422, f"Champ requis manquant: {field}")

    try:
        start = date.fromisoformat(data["start_date"])
        end   = date.fromisoformat(data["end_date"])
    except (ValueError, TypeError):
        raise HTTPException(400, "Format de date invalide. Utilisez YYYY-MM-DD")

    if end <= start:
        raise HTTPException(400, "La date de fin doit être après la date de début")

    days   = (end - start).days
    car_id = int(data["car_id"])

    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        c = conn.cursor()
        c.execute("SELECT * FROM cars WHERE id = ? AND owner_id = ?", (car_id, owner_id))
        car = c.fetchone()
        if not car:
            conn.rollback(); conn.close()
            raise HTTPException(404, "Voiture introuvable")
        if car["status"] != "available":
            conn.rollback(); conn.close()
            raise HTTPException(400, "Cette voiture n'est pas disponible")

        c.execute("""
            SELECT id FROM bookings
            WHERE car_id = ? AND owner_id = ? AND status = 'confirmed'
              AND NOT (end_date < ? OR start_date > ?)
        """, (car_id, owner_id, data["start_date"], data["end_date"]))
        if c.fetchone():
            conn.rollback(); conn.close()
            raise HTTPException(409, "Voiture déjà réservée pour ces dates")

        total   = days * car["daily_rate"]
        deposit = float(data.get("deposit_amount", 0) or 0)
        balance = total - deposit

        c.execute("""
            INSERT INTO bookings (car_id, client_name, client_phone, client_email,
                client_cin, start_date, end_date, total_price, deposit_amount,
                deposit_paid, balance_due, payment_method, notes, owner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (car_id, str(data["client_name"]).strip(), str(data["client_phone"]).strip(),
              data.get("client_email") or None, str(data["client_cin"]).strip().upper(),
              data["start_date"], data["end_date"], total, deposit,
              0, balance, data.get("payment_method", "cash"), data.get("notes") or None,
              owner_id))
        conn.commit()
        booking_id = c.lastrowid
        conn.close()
        return {"id": booking_id, "total_price": total, "days": days,
                "deposit_amount": deposit, "balance_due": balance, "message": "Réservation confirmée"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback(); conn.close()
        raise HTTPException(500, f"Erreur: {str(e)}")


@router.get("/{booking_id}")
def get_booking(booking_id: int, admin=Depends(require_admin)):
    owner_id = _owner(admin)
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT b.*, c.brand, c.model, c.license_plate, c.daily_rate
        FROM bookings b JOIN cars c ON b.car_id = c.id
        WHERE b.id = ? AND b.owner_id = ?
    """, (booking_id, owner_id))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Réservation introuvable")
    return dict(row)


@router.put("/{booking_id}")
def update_booking(booking_id: int, update: BookingUpdate, admin=Depends(require_admin)):
    owner_id = _owner(admin)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE id = ? AND owner_id = ?", (booking_id, owner_id))
    booking = c.fetchone()
    if not booking:
        conn.close(); raise HTTPException(404, "Réservation introuvable")
    if booking["status"] not in {"confirmed", "completed"}:
        conn.close(); raise HTTPException(400, "Impossible de modifier une réservation annulée")

    car_id    = update.car_id or booking["car_id"]
    new_start = update.start_date or booking["start_date"]
    new_end   = update.end_date   or booking["end_date"]

    c.execute("SELECT * FROM cars WHERE id = ? AND owner_id = ?", (car_id, owner_id))
    car = c.fetchone()
    if not car:
        conn.close(); raise HTTPException(404, "Voiture introuvable")

    start = date.fromisoformat(new_start)
    end   = date.fromisoformat(new_end)
    if end <= start:
        conn.close(); raise HTTPException(400, "La date de fin doit être après la date de début")

    days = (end - start).days
    c.execute("""
        SELECT id FROM bookings
        WHERE car_id = ? AND owner_id = ? AND status = 'confirmed' AND id != ?
          AND NOT (end_date < ? OR start_date > ?)
    """, (car_id, owner_id, booking_id, new_start, new_end))
    if c.fetchone():
        conn.close(); raise HTTPException(409, "Voiture déjà réservée pour ces dates")

    total         = days * car["daily_rate"]
    deposit_paid  = update.deposit_paid if update.deposit_paid is not None else booking["deposit_paid"]
    balance       = total - deposit_paid

    updates, values = [], []
    for field, val in {
        "car_id": update.car_id, "client_name": update.client_name,
        "client_phone": update.client_phone, "client_email": update.client_email,
        "client_cin": update.client_cin, "start_date": update.start_date,
        "end_date": update.end_date, "payment_method": update.payment_method,
        "notes": update.notes,
    }.items():
        if val is not None:
            updates.append(f"{field} = ?"); values.append(val)

    updates += ["total_price = ?", "deposit_paid = ?", "balance_due = ?"]
    values  += [total, deposit_paid, balance, booking_id]
    c.execute(f"UPDATE bookings SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit(); conn.close()
    return {"message": "Réservation mise à jour", "total_price": total, "days": days, "balance_due": balance}


@router.patch("/{booking_id}/payment")
def update_payment(booking_id: int, update: PaymentUpdate, admin=Depends(require_admin)):
    owner_id = _owner(admin)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT total_price FROM bookings WHERE id = ? AND owner_id = ?", (booking_id, owner_id))
    row = c.fetchone()
    if not row:
        conn.close(); raise HTTPException(404, "Réservation introuvable")
    balance = row["total_price"] - update.deposit_paid
    c.execute("UPDATE bookings SET deposit_paid = ?, balance_due = ? WHERE id = ?",
              (update.deposit_paid, balance, booking_id))
    if update.payment_method:
        c.execute("UPDATE bookings SET payment_method = ? WHERE id = ?", (update.payment_method, booking_id))
    conn.commit(); conn.close()
    return {"message": "Paiement mis à jour", "balance_due": balance}


@router.patch("/{booking_id}/confirm")
def confirm_booking(booking_id: int, admin=Depends(require_admin)):
    """Admin confirme une demande de réservation client (pending → confirmed)."""
    owner_id = _owner(admin)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, status FROM bookings WHERE id = ? AND owner_id = ?", (booking_id, owner_id))
    row = c.fetchone()
    if not row:
        conn.close(); raise HTTPException(404, "Réservation introuvable")
    if row["status"] != "pending":
        conn.close(); raise HTTPException(400, "Seules les demandes en attente peuvent être confirmées")
    c.execute("UPDATE bookings SET status = 'confirmed' WHERE id = ?", (booking_id,))
    conn.commit(); conn.close()
    return {"message": "Réservation confirmée"}


@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: int, admin=Depends(require_admin)):
    owner_id = _owner(admin)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, status FROM bookings WHERE id = ? AND owner_id = ?", (booking_id, owner_id))
    row = c.fetchone()
    if not row:
        conn.close(); raise HTTPException(404, "Réservation introuvable")
    if row["status"] == "cancelled":
        conn.close(); raise HTTPException(400, "Déjà annulée")
    c.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
    conn.commit(); conn.close()
    return {"message": "Réservation annulée"}


@router.patch("/{booking_id}/complete")
def complete_booking(booking_id: int, admin=Depends(require_admin)):
    owner_id = _owner(admin)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, status FROM bookings WHERE id = ? AND owner_id = ?", (booking_id, owner_id))
    row = c.fetchone()
    if not row:
        conn.close(); raise HTTPException(404, "Réservation introuvable")
    if row["status"] != "confirmed":
        conn.close(); raise HTTPException(400, "Seules les réservations confirmées peuvent être terminées")
    c.execute("UPDATE bookings SET status = 'completed' WHERE id = ?", (booking_id,))
    conn.commit(); conn.close()
    return {"message": "Réservation terminée"}
