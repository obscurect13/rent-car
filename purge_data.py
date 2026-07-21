"""
Script de purge des voitures et réservations.
Lance via :
    docker compose cp purge_data.py backend:/app/purge_data.py
    docker compose exec backend python3 purge_data.py
"""
import sqlite3, os

DB_PATH = os.environ.get("DB_PATH", "/app/data/rental.db")

def purge():
    print("═══════════════════════════════════════")
    print("   Purge des données — AutoLoc Pro")
    print("═══════════════════════════════════════")

    confirm = input("\n⚠️  Cette action supprime TOUTES les voitures et réservations.\nTaper 'CONFIRMER' pour continuer : ").strip()
    if confirm != "CONFIRMER":
        print("❌ Annulé.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    counts = {}
    for tbl in ["cars", "bookings", "inspections", "insurance_tracking", "payments"]:
        if tbl in tables:
            counts[tbl] = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]

    print("\nDonnées trouvées :")
    for tbl, n in counts.items():
        print(f"  {tbl:<25} {n} ligne(s)")

    for tbl in ["inspections", "insurance_tracking", "payments", "bookings", "cars"]:
        if tbl in tables:
            c.execute(f"DELETE FROM {tbl}")
            print(f"  ✅ {tbl} vidé")

    # Reset auto-increment
    c.execute("DELETE FROM sqlite_sequence WHERE name IN ('cars','bookings','inspections','insurance_tracking','payments')")

    conn.commit()
    conn.close()

    print("\n✅ Purge terminée. Les comptes utilisateurs sont conservés.")

if __name__ == "__main__":
    purge()
