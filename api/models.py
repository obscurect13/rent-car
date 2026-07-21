"""Pydantic models for request/response validation"""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date
from api.validators import (
    validate_license_plate, validate_cin, validate_phone, validate_email,
    VALID_CAR_STATUSES, VALID_PAYMENT_METHODS
)


# ── Car Models ───────────────────────────────────────────────────────────────

class CarCreate(BaseModel):
    brand: str
    model: str
    year: int
    mileage: int
    fuel_type: str
    transmission: str
    color: str
    seats: int
    daily_rate: float
    license_plate: str
    category: str
    status: Optional[str] = "available"
    notes: Optional[str] = None

    @field_validator("license_plate")
    @classmethod
    def _validate_plate(cls, v: str) -> str:
        return validate_license_plate(v)

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: Optional[str]) -> str:
        if v is None:
            return "available"
        v = v.lower().strip()
        if v not in VALID_CAR_STATUSES:
            raise ValueError(f"Statut invalide. Valeurs: {', '.join(VALID_CAR_STATUSES)}")
        return v

    @field_validator("year")
    @classmethod
    def _validate_year(cls, v: int) -> int:
        current_year = date.today().year
        if v < 1990 or v > current_year + 1:
            raise ValueError(f"Année invalide. Doit être entre 1990 et {current_year + 1}")
        return v

    @field_validator("daily_rate")
    @classmethod
    def _validate_rate(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Le tarif journalier doit être supérieur à 0")
        return v

    @field_validator("mileage")
    @classmethod
    def _validate_mileage(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Le kilométrage ne peut pas être négatif")
        return v

    @field_validator("seats")
    @classmethod
    def _validate_seats(cls, v: int) -> int:
        if v < 2 or v > 50:
            raise ValueError("Le nombre de places doit être entre 2 et 50")
        return v


class CarUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    color: Optional[str] = None
    seats: Optional[int] = None
    daily_rate: Optional[float] = None
    license_plate: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("license_plate")
    @classmethod
    def _validate_plate(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_license_plate(v)

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.lower().strip()
        if v not in VALID_CAR_STATUSES:
            raise ValueError(f"Statut invalide. Valeurs: {', '.join(VALID_CAR_STATUSES)}")
        return v

    @field_validator("year")
    @classmethod
    def _validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        current_year = date.today().year
        if v < 1990 or v > current_year + 1:
            raise ValueError(f"Année invalide. Doit être entre 1990 et {current_year + 1}")
        return v

    @field_validator("daily_rate")
    @classmethod
    def _validate_rate(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("Le tarif journalier doit être supérieur à 0")
        return v


class CarStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_CAR_STATUSES:
            raise ValueError(f"Statut invalide. Valeurs: {', '.join(VALID_CAR_STATUSES)}")
        return v


# ── Booking Models ─────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    car_id: int
    client_name: str
    client_phone: str
    client_email: Optional[str] = None
    client_cin: str
    start_date: str
    end_date: str
    deposit_amount: Optional[float] = 0
    payment_method: Optional[str] = "cash"
    notes: Optional[str] = None

    @field_validator("client_name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Le nom du client doit contenir au moins 2 caractères")
        return v

    @field_validator("client_phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        return validate_phone(v)

    @field_validator("client_cin")
    @classmethod
    def _validate_cin(cls, v: str) -> str:
        return validate_cin(v)

    @field_validator("client_email")
    @classmethod
    def _validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        try:
            return validate_email(v.strip())
        except ValueError:
            return None

    @field_validator("start_date", "end_date")
    @classmethod
    def _validate_dates(cls, v: str) -> str:
        if v is None:
            raise ValueError("La date est requise")
        try:
            date.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError("Format de date invalide. Utilisez YYYY-MM-DD")
        return v

    @field_validator("deposit_amount")
    @classmethod
    def _validate_deposit(cls, v: Optional[float]) -> float:
        if v is None:
            return 0
        if v < 0:
            raise ValueError("L'acompte ne peut pas être négatif")
        return v

    @field_validator("payment_method")
    @classmethod
    def _validate_payment_method(cls, v: Optional[str]) -> str:
        if v is None:
            return "cash"
        v = v.lower().strip()
        if v not in VALID_PAYMENT_METHODS:
            raise ValueError(f"Méthode invalide. Valeurs: {', '.join(VALID_PAYMENT_METHODS)}")
        return v


class BookingUpdate(BaseModel):
    """For modifying existing bookings (dates, car, client info)"""
    car_id: Optional[int] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    client_cin: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    deposit_paid: Optional[float] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("client_name")
    @classmethod
    def _validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Le nom du client doit contenir au moins 2 caractères")
        return v

    @field_validator("client_phone")
    @classmethod
    def _validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_phone(v)

    @field_validator("client_cin")
    @classmethod
    def _validate_cin(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_cin(v)

    @field_validator("client_email")
    @classmethod
    def _validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        return validate_email(v.strip())

    @field_validator("deposit_paid")
    @classmethod
    def _validate_deposit_paid(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if v < 0:
            raise ValueError("Le montant payé ne peut pas être négatif")
        return v


class PaymentUpdate(BaseModel):
    deposit_paid: float
    payment_method: Optional[str] = None

    @field_validator("deposit_paid")
    @classmethod
    def _validate_deposit_paid(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Le montant payé ne peut pas être négatif")
        return v

    @field_validator("payment_method")
    @classmethod
    def _validate_payment_method(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.lower().strip()
        if v not in VALID_PAYMENT_METHODS:
            raise ValueError(f"Méthode invalide. Valeurs: {', '.join(VALID_PAYMENT_METHODS)}")
        return v


# ── Inspection Models ──────────────────────────────────────────────────────

class InspectionCreate(BaseModel):
    booking_id: int
    return_date: str
    fuel_level: Optional[int] = None  # 0-100
    mileage: Optional[int] = None
    tires_ok: Optional[int] = 1
    lights_ok: Optional[int] = 1
    body_damage: Optional[str] = None
    interior_clean: Optional[int] = 1
    documents_ok: Optional[int] = 1
    spare_tire_ok: Optional[int] = 1
    jack_tools_ok: Optional[int] = 1
    damage_photos: Optional[str] = None
    damage_cost: Optional[float] = 0
    notes: Optional[str] = None

    @field_validator("fuel_level")
    @classmethod
    def _validate_fuel(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v < 0 or v > 100:
            raise ValueError("Le niveau de carburant doit être entre 0 et 100")
        return v

    @field_validator("damage_cost")
    @classmethod
    def _validate_damage_cost(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return 0
        if v < 0:
            raise ValueError("Le coût des dommages ne peut pas être négatif")
        return v


# ── Insurance Models ─────────────────────────────────────────────────────────

class InsuranceCreate(BaseModel):
    car_id: int
    insurance_type: str
    provider: Optional[str] = None
    policy_number: Optional[str] = None
    start_date: str
    expiry_date: str
    cost: Optional[float] = 0
    notes: Optional[str] = None

    @field_validator("insurance_type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        v = v.strip().lower()
        valid_types = {"assurance", "vignette", "assistance", "tous_risques"}
        if v not in valid_types:
            raise ValueError(f"Type invalide. Valeurs: {', '.join(valid_types)}")
        return v

    @field_validator("start_date", "expiry_date")
    @classmethod
    def _validate_dates(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("Format de date invalide. Utilisez YYYY-MM-DD")
        return v


class InsuranceUpdate(BaseModel):
    provider: Optional[str] = None
    policy_number: Optional[str] = None
    expiry_date: Optional[str] = None
    cost: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
