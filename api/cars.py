"""Car management endpoints — multi-tenant (filtered by owner_id)"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import sqlite3
from api.database import get_db
from api.models import CarCreate, CarUpdate, CarStatusUpdate
from api.auth import require_admin

router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("", response_model=List[dict])
def list_cars(
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    admin=Depends(require_admin)
):
    owner_id = int(admin["sub"])
    conn = get_db()
    c = conn.cursor()

    query = "SELECT * FROM cars WHERE owner_id = ?"
    params = [owner_id]

    if status:
        query += " AND status = ?"
        params.append(status)
    if search:
        t = f"%{search}%"
        query += " AND (brand LIKE ? OR model LIKE ? OR license_plate LIKE ? OR color LIKE ? OR notes LIKE ?)"
        params.extend([t, t, t, t, t])

    sort_map = {
        "price_asc": ("daily_rate", "ASC"), "price_desc": ("daily_rate", "DESC"),
        "year_asc": ("year", "ASC"), "year_desc": ("year", "DESC"),
        "mileage_asc": ("mileage", "ASC"), "mileage_desc": ("mileage", "DESC"),
        "brand_asc": ("brand", "ASC"),
    }
    sf, so = sort_map.get(sort_by or "", ("created_at", "DESC"))
    query += f" ORDER BY {sf} {so}"

    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@router.post("", status_code=201)
def add_car(car: CarCreate, admin=Depends(require_admin)):
    owner_id = int(admin["sub"])
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO cars (brand, model, year, mileage, fuel_type, transmission,
                color, seats, daily_rate, license_plate, category, status, notes, owner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (car.brand, car.model, car.year, car.mileage, car.fuel_type,
              car.transmission, car.color, car.seats, car.daily_rate,
              car.license_plate, car.category, car.status, car.notes, owner_id))
        conn.commit()
        car_id = c.lastrowid
        conn.close()
        return {"id": car_id, "message": "Voiture ajoutée avec succès"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Plaque d'immatriculation déjà existante")


@router.get("/search/available")
def available_cars(start_date: str, end_date: str, admin=Depends(require_admin)):
    from datetime import date as dt
    try:
        start = dt.fromisoformat(start_date)
        end   = dt.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(400, "Format de date invalide. Utilisez YYYY-MM-DD")
    if end <= start:
        raise HTTPException(400, "La date de fin doit être après la date de début")

    owner_id = int(admin["sub"])
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM cars
        WHERE owner_id = ? AND status = 'available'
          AND id NOT IN (
              SELECT car_id FROM bookings
              WHERE owner_id = ? AND status = 'confirmed'
                AND NOT (end_date < ? OR start_date > ?)
          )
        ORDER BY daily_rate ASC
    """, (owner_id, owner_id, start_date, end_date))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@router.get("/{car_id}")
def get_car(car_id: int, admin=Depends(require_admin)):
    owner_id = int(admin["sub"])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM cars WHERE id = ? AND owner_id = ?", (car_id, owner_id))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Voiture introuvable")
    return dict(row)


@router.put("/{car_id}")
def update_car(car_id: int, car: CarUpdate, admin=Depends(require_admin)):
    owner_id = int(admin["sub"])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM cars WHERE id = ? AND owner_id = ?", (car_id, owner_id))
    if not c.fetchone():
        conn.close()
        raise HTTPException(404, "Voiture introuvable")

    updates, values = [], []
    fields = {
        "brand": car.brand, "model": car.model, "year": car.year,
        "mileage": car.mileage, "fuel_type": car.fuel_type,
        "transmission": car.transmission, "color": car.color,
        "seats": car.seats, "daily_rate": car.daily_rate,
        "license_plate": car.license_plate, "category": car.category,
        "status": car.status, "notes": car.notes
    }
    for field, value in fields.items():
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        conn.close()
        raise HTTPException(400, "Aucun champ à mettre à jour")

    values.append(car_id)
    try:
        c.execute(f"UPDATE cars SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
        conn.close()
        return {"message": "Voiture mise à jour avec succès"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Plaque d'immatriculation déjà existante")


@router.patch("/{car_id}/status")
def update_car_status(car_id: int, update: CarStatusUpdate, admin=Depends(require_admin)):
    owner_id = int(admin["sub"])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM cars WHERE id = ? AND owner_id = ?", (car_id, owner_id))
    if not c.fetchone():
        conn.close()
        raise HTTPException(404, "Voiture introuvable")
    c.execute("UPDATE cars SET status = ? WHERE id = ?", (update.status, car_id))
    conn.commit()
    conn.close()
    return {"message": f"Statut mis à jour: {update.status}"}


@router.delete("/{car_id}")
def delete_car(car_id: int, admin=Depends(require_admin)):
    owner_id = int(admin["sub"])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM cars WHERE id = ? AND owner_id = ?", (car_id, owner_id))
    if not c.fetchone():
        conn.close()
        raise HTTPException(404, "Voiture introuvable")
    c.execute("""
        SELECT id FROM bookings
        WHERE car_id = ? AND owner_id = ? AND status = 'confirmed'
        AND end_date >= date('now')
    """, (car_id, owner_id))
    if c.fetchone():
        conn.close()
        raise HTTPException(409, "Impossible de supprimer: réservations actives associées")
    c.execute("DELETE FROM cars WHERE id = ?", (car_id,))
    conn.commit()
    conn.close()
    return {"message": "Voiture supprimée"}
