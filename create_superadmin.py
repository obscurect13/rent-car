"""
Script de création du compte superadmin.
À exécuter UNE SEULE FOIS via :
    docker compose exec backend python3 create_superadmin.py
"""
import sys, os, sqlite3

# ── Dépendances ──────────────────────────────────────────────────────────
try:
    from passlib.context import CryptContext
except ImportError:
    print("❌ passlib non installé")
    sys.exit(1)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB_PATH = os.environ.get("DB_PATH", "/app/data/rental.db")

def create():
    print("═══════════════════════════════════════")
    print("   Création du compte SuperAdmin")
    print("═══════════════════════════════════════")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Vérifier si un superadmin existe déjà
    existing = conn.execute(
        "SELECT id, email FROM users WHERE role = 'superadmin'"
    ).fetchone()
    if existing:
        print(f"⚠️  Un superadmin existe déjà : {existing['email']} (id={existing['id']})")
        print("Abandonné — un seul superadmin est autorisé.")
        conn.close()
        return

    # Saisie interactive
    print("\nRenseignez les informations du superadmin :\n")
    full_name = input("Nom complet      : ").strip()
    email     = input("Email            : ").strip().lower()
    password  = input("Mot de passe     : ").strip()

    if not full_name or not email or not password:
        print("❌ Tous les champs sont obligatoires.")
        conn.close()
        return

    if len(password) < 6:
        print("❌ Mot de passe trop court (6 caractères minimum).")
        conn.close()
        return

    if "@" not in email:
        print("❌ Email invalide.")
        conn.close()
        return

    # Vérifier email unique
    existing_email = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()
    if existing_email:
        print(f"❌ Email déjà utilisé par le compte id={existing_email['id']}.")
        conn.close()
        return

    # Créer le superadmin
    hashed = pwd_ctx.hash(password)
    conn.execute(
        "INSERT INTO users (full_name, email, password, role) VALUES (?, ?, ?, 'superadmin')",
        (full_name, email, hashed)
    )
    conn.commit()
    row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    print(f"\n✅ Superadmin créé avec succès !")
    print(f"   ID       : {row['id']}")
    print(f"   Nom      : {full_name}")
    print(f"   Email    : {email}")
    print(f"   Rôle     : superadmin")
    print("\n⚠️  Gardez ces identifiants en sécurité.")

if __name__ == "__main__":
    create()
