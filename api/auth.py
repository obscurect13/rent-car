"""Authentication router — register / login / JWT — with superadmin support"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from passlib.context import CryptContext
from jose import JWTError, jwt

from api.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "autoloc-secret-key-change-in-production-2024"
ALGORITHM  = "HS256"
TOKEN_EXP  = 60 * 24  # 24h

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer  = HTTPBearer(auto_error=False)

ROLES = ("superadmin", "admin", "user")


def init_users_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name  TEXT    NOT NULL,
            email      TEXT    UNIQUE NOT NULL,
            phone      TEXT,
            cin        TEXT,
            password   TEXT    NOT NULL,
            role       TEXT    NOT NULL DEFAULT 'user',
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)
    # Migration: add role column if missing
    cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    conn.commit()
    conn.close()

init_users_table()


# ── Schemas ───────────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    cin: Optional[str] = None
    password: str
    role: str = "user"

    @field_validator("role")
    @classmethod
    def _role(cls, v):
        # Public registration only allows admin or user — never superadmin
        if v not in ("admin", "user"):
            raise ValueError("Rôle invalide")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        v = v.strip().lower()
        if "@" not in v:
            raise ValueError("Email invalide")
        return v

    @field_validator("password")
    @classmethod
    def _pwd(cls, v):
        if len(v) < 6:
            raise ValueError("Mot de passe : 6 caractères minimum")
        return v

class LoginIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


# ── Helpers ───────────────────────────────────────────────────────────────
def hash_password(pwd: str) -> str:
    return pwd_ctx.hash(pwd)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=TOKEN_EXP)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)):
    if not creds:
        raise HTTPException(401, "Non authentifié")
    try:
        return decode_token(creds.credentials)
    except JWTError:
        raise HTTPException(401, "Token invalide ou expiré")

def require_admin(user=Depends(get_current_user)):
    """Allows admin AND superadmin."""
    if user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(403, "Accès réservé aux administrateurs")
    return user

def require_superadmin(user=Depends(get_current_user)):
    """Allows ONLY superadmin."""
    if user.get("role") != "superadmin":
        raise HTTPException(403, "Accès réservé au super-administrateur")
    return user


# ── Public routes ─────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (full_name, email, phone, cin, password, role) VALUES (?,?,?,?,?,?)",
            (body.full_name, body.email, body.phone, body.cin,
             hash_password(body.password), body.role)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE email=?", (body.email,)).fetchone()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(409, "Un compte avec cet email existe déjà")
    conn.close()
    token = create_token({"sub": str(row["id"]), "role": row["role"], "name": row["full_name"]})
    return TokenOut(access_token=token, role=row["role"],
                    full_name=row["full_name"], user_id=row["id"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email=?", (body.email.strip().lower(),)).fetchone()
    conn.close()
    if not row or not verify_password(body.password, row["password"]):
        raise HTTPException(401, "Email ou mot de passe incorrect")
    token = create_token({"sub": str(row["id"]), "role": row["role"], "name": row["full_name"]})
    return TokenOut(access_token=token, role=row["role"],
                    full_name=row["full_name"], user_id=row["id"])


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user


# ── Superadmin only : gestion des comptes ─────────────────────────────────
@router.get("/users")
def list_users(user=Depends(require_superadmin)):
    """Liste tous les comptes — superadmin uniquement."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, full_name, email, phone, cin, role, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.patch("/users/{user_id}/role")
def change_role(user_id: int, body: dict, user=Depends(require_superadmin)):
    """Change le rôle d'un compte — superadmin uniquement."""
    new_role = body.get("role")
    if new_role not in ("admin", "user"):
        raise HTTPException(400, "Rôle invalide — 'admin' ou 'user'")
    conn = get_db()
    row = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Utilisateur introuvable")
    if row["role"] == "superadmin":
        conn.close()
        raise HTTPException(400, "Impossible de modifier le rôle superadmin")
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()
    return {"message": f"Rôle mis à jour : {new_role}"}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, user=Depends(require_superadmin)):
    """Supprime un compte — superadmin uniquement."""
    if str(user_id) == user.get("sub"):
        raise HTTPException(400, "Vous ne pouvez pas supprimer votre propre compte")
    conn = get_db()
    row = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Utilisateur introuvable")
    if row["role"] == "superadmin":
        conn.close()
        raise HTTPException(400, "Impossible de supprimer un superadmin")
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "Compte supprimé"}
