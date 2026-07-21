"""Input validators and regex patterns"""
import re

# License plate: 12345-A-1
LICENSE_PLATE_PATTERN = re.compile(r"^[0-9]{1,6}-[A-Z]-[0-9]{1,2}$")

# CIN: AB123456
CIN_PATTERN = re.compile(r"^[A-Z]{1,2}[0-9]{4,6}$")

# Phone: 8-20 chars, digits, spaces, +, -
PHONE_PATTERN = re.compile(r"^[0-9+\s-]{8,20}$")

# Email
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

VALID_CAR_STATUSES = {"available", "maintenance", "retired"}
VALID_BOOKING_STATUSES = {"confirmed", "cancelled", "completed"}
VALID_PAYMENT_METHODS = {"cash", "card", "transfer", "deposit"}
VALID_INSPECTION_ITEMS = {
    "fuel_level", "mileage", "tires", "lights", "body_damage",
    "interior_clean", "documents", "spare_tire", "jack_tools"
}


def validate_license_plate(v: str) -> str:
    v = v.strip().upper()
    if not LICENSE_PLATE_PATTERN.match(v):
        raise ValueError("Format de plaque invalide. Exemple: 12345-A-1")
    return v


def validate_cin(v: str) -> str:
    v = v.strip().upper()
    if not CIN_PATTERN.match(v):
        raise ValueError("Format CIN invalide. Exemple: AB123456")
    return v


def validate_phone(v: str) -> str:
    v = v.strip()
    if not PHONE_PATTERN.match(v):
        raise ValueError("Numéro de téléphone invalide")
    return v


def validate_email(v: str) -> str:
    v = v.strip()
    if not EMAIL_PATTERN.match(v):
        raise ValueError("Format d'email invalide")
    return v
