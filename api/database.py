"""Database connection and initialization"""
import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "../data/rental.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db():
    """Get a database connection with row factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database tables and triggers."""
    conn = get_db()
    c = conn.cursor()

    # Cars table
    c.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            mileage INTEGER NOT NULL,
            fuel_type TEXT NOT NULL,
            transmission TEXT NOT NULL,
            color TEXT NOT NULL,
            seats INTEGER NOT NULL,
            daily_rate REAL NOT NULL,
            license_plate TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            notes TEXT,
            owner_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Bookings table with payment tracking
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            client_phone TEXT NOT NULL,
            client_email TEXT,
            client_cin TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            total_price REAL NOT NULL,
            deposit_amount REAL DEFAULT 0,
            deposit_paid REAL DEFAULT 0,
            balance_due REAL DEFAULT 0,
            payment_method TEXT,
            status TEXT DEFAULT 'confirmed',
            notes TEXT,
            user_id INTEGER,
            owner_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE RESTRICT
        )
    """)

    # Return inspections table
    c.execute("""
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            return_date TEXT NOT NULL,
            fuel_level INTEGER CHECK(fuel_level BETWEEN 0 AND 100),
            mileage INTEGER,
            tires_ok INTEGER DEFAULT 1,
            lights_ok INTEGER DEFAULT 1,
            body_damage TEXT,
            interior_clean INTEGER DEFAULT 1,
            documents_ok INTEGER DEFAULT 1,
            spare_tire_ok INTEGER DEFAULT 1,
            jack_tools_ok INTEGER DEFAULT 1,
            damage_photos TEXT,
            damage_cost REAL DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
        )
    """)

    # Insurance & vignette tracking table
    c.execute("""
        CREATE TABLE IF NOT EXISTS insurance_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            insurance_type TEXT NOT NULL,
            provider TEXT,
            policy_number TEXT,
            start_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cost REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
        )
    """)

    # Trigger: auto-update cars.updated_at
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS cars_updated_at
        AFTER UPDATE ON cars
        FOR EACH ROW
        BEGIN
            UPDATE cars SET updated_at = datetime('now') WHERE id = NEW.id;
        END
    """)

    # Trigger: auto-update bookings.updated_at
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS bookings_updated_at
        AFTER UPDATE ON bookings
        FOR EACH ROW
        BEGIN
            UPDATE bookings SET updated_at = datetime('now') WHERE id = NEW.id;
        END
    """)

    # Trigger: auto-update insurance_tracking.updated_at
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS insurance_updated_at
        AFTER UPDATE ON insurance_tracking
        FOR EACH ROW
        BEGIN
            UPDATE insurance_tracking SET updated_at = datetime('now') WHERE id = NEW.id;
        END
    """)


    # Migration: add owner_id if missing
    for tbl in ("cars", "bookings", "inspections", "insurance_tracking"):
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({tbl})").fetchall()]
        if "owner_id" not in cols:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN owner_id INTEGER")

    # Migration: add user_id to bookings if missing
    cols = [r[1] for r in c.execute("PRAGMA table_info(bookings)").fetchall()]
    if "user_id" not in cols:
        c.execute("ALTER TABLE bookings ADD COLUMN user_id INTEGER")

    conn.commit()

    conn.commit()
    conn.close()


# Initialize on import
init_db()
