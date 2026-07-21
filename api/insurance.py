"""Insurance and vignette tracking endpoints"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import date, timedelta
from api.database import get_db
from api.models import InsuranceCreate, InsuranceUpdate

router = APIRouter(prefix="/insurance", tags=["insurance"])


@router.get("/car/{car_id}")
def get_car_insurance(car_id: int):
    """Get all insurance/vignette records for a car."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM insurance_tracking
        WHERE car_id = ?
        ORDER BY expiry_date ASC
    """, (car_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@router.get("/car/{car_id}/active")
def get_active_insurance(car_id: int):
    """Get active insurance/vignette for a car."""
    conn = get_db()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        SELECT * FROM insurance_tracking
        WHERE car_id = ? AND status = 'active' AND expiry_date >= ?
        ORDER BY expiry_date ASC
    """, (car_id, today))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@router.post("")
def create_insurance_record(record: InsuranceCreate):
    """Create an insurance/vignette record."""
    conn = get_db()
    c = conn.cursor()

    # Verify car exists
    c.execute("SELECT id FROM cars WHERE id = ?", (record.car_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(404, "Voiture introuvable")

    c.execute("""
        INSERT INTO insurance_tracking (car_id, insurance_type, provider,
            policy_number, start_date, expiry_date, cost, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (record.car_id, record.insurance_type, record.provider,
          record.policy_number, record.start_date, record.expiry_date,
          record.cost, record.notes))

    conn.commit()
    record_id = c.lastrowid
    conn.close()
    return {"id": record_id, "message": "Enregistrement créé"}


@router.put("/{record_id}")
def update_insurance_record(record_id: int, update: InsuranceUpdate):
    """Update an insurance record."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM insurance_tracking WHERE id = ?", (record_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(404, "Enregistrement non trouvé")

    updates = []
    values = []
    fields = {
        "provider": update.provider, "policy_number": update.policy_number,
        "expiry_date": update.expiry_date, "cost": update.cost,
        "status": update.status, "notes": update.notes
    }
    for field, value in fields.items():
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        conn.close()
        raise HTTPException(400, "Aucun champ à mettre à jour")

    values.append(record_id)
    c.execute(f"UPDATE insurance_tracking SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Enregistrement mis à jour"}


@router.delete("/{record_id}")
def delete_insurance_record(record_id: int):
    """Delete an insurance record."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM insurance_tracking WHERE id = ?", (record_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(404, "Enregistrement non trouvé")
    c.execute("DELETE FROM insurance_tracking WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return {"message": "Enregistrement supprimé"}


@router.get("/alerts/expiring")
def get_expiring_insurance(days: int = 30):
    """Get insurance/vignette expiring within X days."""
    conn = get_db()
    c = conn.cursor()
    alert_date = (date.today() + timedelta(days=days)).isoformat()
    today = date.today().isoformat()
    c.execute("""
        SELECT i.*, c.brand, c.model, c.license_plate
        FROM insurance_tracking i
        JOIN cars c ON i.car_id = c.id
        WHERE i.status = 'active' AND i.expiry_date <= ? AND i.expiry_date >= ?
        ORDER BY i.expiry_date ASC
    """, (alert_date, today))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@router.get("/alerts/expired")
def get_expired_insurance():
    """Get expired insurance/vignette."""
    conn = get_db()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        SELECT i.*, c.brand, c.model, c.license_plate
        FROM insurance_tracking i
        JOIN cars c ON i.car_id = c.id
        WHERE i.status = 'active' AND i.expiry_date < ?
        ORDER BY i.expiry_date ASC
    """, (today,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


@router.get("/stats")
def get_insurance_stats():
    """Get insurance statistics."""
    conn = get_db()
    c = conn.cursor()
    today = date.today().isoformat()

    c.execute("SELECT COUNT(*) as total FROM insurance_tracking WHERE status = 'active'")
    total_active = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as expiring FROM insurance_tracking WHERE status = 'active' AND expiry_date < ?", (today,))
    expired = c.fetchone()["expiring"]

    alert_date = (date.today() + timedelta(days=30)).isoformat()
    c.execute("SELECT COUNT(*) as expiring FROM insurance_tracking WHERE status = 'active' AND expiry_date BETWEEN ? AND ?", (today, alert_date))
    expiring_soon = c.fetchone()["expiring"]

    conn.close()
    return {
        "total_active": total_active,
        "expired": expired,
        "expiring_soon": expiring_soon
    }
