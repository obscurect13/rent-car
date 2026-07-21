"""Export endpoints (CSV and PDF)"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import csv
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from api.database import get_db

router = APIRouter(prefix="/export", tags=["exports"])


@router.get("/cars")
def export_cars_csv():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM cars ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Marque", "Modèle", "Année", "Kilométrage", "Carburant",
                     "Transmission", "Couleur", "Places", "Tarif/jour", "Plaque",
                     "Catégorie", "Statut", "Notes", "Créé le"])
    for r in rows:
        writer.writerow([r["id"], r["brand"], r["model"], r["year"], r["mileage"],
                         r["fuel_type"], r["transmission"], r["color"], r["seats"],
                         r["daily_rate"], r["license_plate"], r["category"],
                         r["status"], r["notes"], r["created_at"]])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=parc_automobile.csv"}
    )


@router.get("/bookings")
def export_bookings_csv(status: Optional[str] = None):
    conn = get_db()
    c = conn.cursor()
    query = """
        SELECT b.*, c.brand, c.model, c.license_plate
        FROM bookings b JOIN cars c ON b.car_id = c.id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND b.status = ?"
        params.append(status)
    query += " ORDER BY b.created_at DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Client", "Téléphone", "Email", "CIN", "Véhicule",
                     "Plaque", "Début", "Fin", "Jours", "Total (MAD)", "Acompte",
                     "Payé", "Solde", "Méthode", "Statut", "Notes", "Créé le"])
    for r in rows:
        days = (date.fromisoformat(r["end_date"]) - date.fromisoformat(r["start_date"])).days
        writer.writerow([r["id"], r["client_name"], r["client_phone"], r["client_email"],
                         r["client_cin"], f"{r['brand']} {r['model']}", r["license_plate"],
                         r["start_date"], r["end_date"], days, r["total_price"],
                         r["deposit_amount"], r["deposit_paid"], r["balance_due"],
                         r["payment_method"], r["status"], r["notes"], r["created_at"]])

    output.seek(0)
    filename = f"reservations_{status or 'toutes'}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/bookings/{booking_id}/contract")
def generate_contract(booking_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT b.*, c.brand, c.model, c.year, c.license_plate, c.color, c.fuel_type,
               c.transmission, c.seats, c.daily_rate
        FROM bookings b JOIN cars c ON b.car_id = c.id
        WHERE b.id = ?
    """, (booking_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, "Réservation introuvable")

    b = dict(row)
    days = (date.fromisoformat(b["end_date"]) - date.fromisoformat(b["start_date"])).days

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                          topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#1E3A5F"),
        spaceAfter=30,
        alignment=1
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=10,
        spaceBefore=15
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    story = []

    # Header
    story.append(Paragraph("<b>CONTRAT DE LOCATION DE VÉHICULE</b>", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Contrat N° {b['id']}</b> — Date: {date.today().strftime('%d/%m/%Y')}", normal_style))
    story.append(Spacer(1, 20))

    # Client info
    story.append(Paragraph("<b>1. INFORMATIONS DU LOCATAIRE</b>", heading_style))
    client_data = [
        ["Nom complet:", b["client_name"]],
        ["CIN:", b["client_cin"]],
        ["Téléphone:", b["client_phone"]],
        ["Email:", b["client_email"] or "N/A"],
    ]
    client_table = Table(client_data, colWidths=[4*cm, 12*cm])
    client_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 15))

    # Vehicle info
    story.append(Paragraph("<b>2. INFORMATIONS DU VÉHICULE</b>", heading_style))
    vehicle_data = [
        ["Marque / Modèle:", f"{b['brand']} {b['model']} ({b['year']})"],
        ["Plaque d'immatriculation:", b["license_plate"]],
        ["Couleur:", b["color"]],
        ["Carburant:", b["fuel_type"]],
        ["Transmission:", b["transmission"]],
        ["Places:", str(b["seats"])],
    ]
    vehicle_table = Table(vehicle_data, colWidths=[4*cm, 12*cm])
    vehicle_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(vehicle_table)
    story.append(Spacer(1, 15))

    # Rental details
    story.append(Paragraph("<b>3. DÉTAILS DE LA LOCATION</b>", heading_style))
    rental_data = [
        ["Date de prise en charge:", b["start_date"]],
        ["Date de restitution:", b["end_date"]],
        ["Durée:", f"{days} jour(s)"],
        ["Tarif journalier:", f"{b['daily_rate']:.2f} MAD"],
        ["Montant total:", f"{b['total_price']:.2f} MAD"],
        ["Acompte versé:", f"{b.get('deposit_paid', 0):.2f} MAD"],
        ["Solde restant:", f"{b.get('balance_due', b['total_price']):.2f} MAD"],
    ]
    rental_table = Table(rental_data, colWidths=[4*cm, 12*cm])
    rental_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor("#DBEAFE")),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
    ]))
    story.append(rental_table)
    story.append(Spacer(1, 15))

    # Terms
    story.append(Paragraph("<b>4. CONDITIONS GÉNÉRALES</b>", heading_style))
    terms = [
        "• Le locataire s'engage à restituer le véhicule à la date et heure convenues.",
        "• Le carburant doit être restitué au même niveau qu'au départ.",
        "• Tout dommage causé par négligence est à la charge du locataire.",
        "• En cas de retard de restitution, un supplément de 50% du tarif journalier sera appliqué par jour.",
        f"• Le kilométrage au départ est de {b.get('mileage', 0):,} km.",
        "• Le locataire doit présenter un permis de conduire valide et une pièce d'identité.",
    ]
    for term in terms:
        story.append(Paragraph(term, normal_style))

    story.append(Spacer(1, 30))

    # Signatures
    sig_data = [
        ["Signature du locataire:", "Signature du loueur:"],
        ["", ""],
        ["_" * 30, "_" * 30],
    ]
    sig_table = Table(sig_data, colWidths=[8*cm, 8*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, 1), 40),
    ]))
    story.append(sig_table)

    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=contrat_location_{booking_id}.pdf"}
    )
