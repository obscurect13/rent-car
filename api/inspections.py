"""Return inspection checklist endpoints"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
from api.database import get_db
from api.models import InspectionCreate

router = APIRouter(prefix="/inspections", tags=["inspections"])


@router.get("/booking/{booking_id}")
def get_inspection(booking_id: int):
    """Get inspection for a specific booking."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inspections WHERE booking_id = ?", (booking_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Inspection non trouvée")
    return dict(row)


@router.post("")
def create_inspection(inspection: InspectionCreate):
    """Create a return inspection checklist."""
    conn = get_db()
    c = conn.cursor()

    # Verify booking exists
    c.execute("SELECT id, status FROM bookings WHERE id = ?", (inspection.booking_id,))
    booking = c.fetchone()
    if not booking:
        conn.close()
        raise HTTPException(404, "Réservation introuvable")
    if booking["status"] not in {"confirmed", "completed"}:
        conn.close()
        raise HTTPException(400, "Impossible d'inspecter une réservation annulée")

    # Check if inspection already exists
    c.execute("SELECT id FROM inspections WHERE booking_id = ?", (inspection.booking_id,))
    if c.fetchone():
        conn.close()
        raise HTTPException(409, "Une inspection existe déjà pour cette réservation")

    c.execute("""
        INSERT INTO inspections (booking_id, return_date, fuel_level, mileage,
            tires_ok, lights_ok, body_damage, interior_clean, documents_ok,
            spare_tire_ok, jack_tools_ok, damage_photos, damage_cost, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (inspection.booking_id, inspection.return_date, inspection.fuel_level,
          inspection.mileage, inspection.tires_ok, inspection.lights_ok,
          inspection.body_damage, inspection.interior_clean, inspection.documents_ok,
          inspection.spare_tire_ok, inspection.jack_tools_ok, inspection.damage_photos,
          inspection.damage_cost, inspection.notes))

    conn.commit()
    inspection_id = c.lastrowid
    conn.close()
    return {"id": inspection_id, "message": "Inspection enregistrée"}


@router.put("/{inspection_id}")
def update_inspection(inspection_id: int, inspection: InspectionCreate):
    """Update an existing inspection."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM inspections WHERE id = ?", (inspection_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(404, "Inspection non trouvée")

    c.execute("""
        UPDATE inspections SET
            return_date = ?, fuel_level = ?, mileage = ?,
            tires_ok = ?, lights_ok = ?, body_damage = ?,
            interior_clean = ?, documents_ok = ?, spare_tire_ok = ?,
            jack_tools_ok = ?, damage_photos = ?, damage_cost = ?, notes = ?
        WHERE id = ?
    """, (inspection.return_date, inspection.fuel_level, inspection.mileage,
          inspection.tires_ok, inspection.lights_ok, inspection.body_damage,
          inspection.interior_clean, inspection.documents_ok, inspection.spare_tire_ok,
          inspection.jack_tools_ok, inspection.damage_photos, inspection.damage_cost,
          inspection.notes, inspection_id))

    conn.commit()
    conn.close()
    return {"message": "Inspection mise à jour"}


@router.get("/stats")
def get_inspection_stats():
    """Get inspection statistics."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM inspections")
    total = c.fetchone()["total"]
    c.execute("SELECT COUNT(*) as damage_count FROM inspections WHERE damage_cost > 0")
    damage_count = c.fetchone()["damage_count"]
    c.execute("SELECT COALESCE(SUM(damage_cost), 0) as total_damage FROM inspections")
    total_damage = c.fetchone()["total_damage"]
    conn.close()
    return {
        "total_inspections": total,
        "damage_incidents": damage_count,
        "total_damage_cost": total_damage
    }
