"""
Patient Data Models
===================
Pydantic schemas for Patient entity validation, serialization, and API responses.
Enforces rigorous healthcare data integrity rules across names, demographics,
clinical identifiers, dates of birth, phone numbers, and emergency contacts.
"""

import re
from typing import Optional, List, Any
from datetime import date
from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationInfo

# Regular Expressions & Supported Option Sets
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\.\(\)]{7,25}$")
NAME_ALLOWED_CHARS = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' \-]+$")
VALID_GENDERS = {"Male", "Female", "Other"}
VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


class PatientBase(BaseModel):
    first_name: str = Field(..., description="Patient given name (min 2 chars)", example="John")
    last_name: str = Field(..., description="Patient family name (min 2 chars)", example="Doe")
    dob: str = Field(..., description="ISO-8601 date YYYY-MM-DD (not in future)", example="1980-05-15")
    gender: str = Field(..., description="Male, Female, or Other", example="Male")
    blood_group: str = Field(..., description="ABO/Rh Blood Group: A+, A-, B+, B-, AB+, AB-, O+, O-", example="O+")
    contact_phone: Optional[str] = Field(None, description="International phone format", example="+1-555-0199")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact person and phone", example="Jane Doe (+1-555-0198)")

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def validate_name(cls, value: Any, info: ValidationInfo) -> str:
        field_label = (info.field_name or "Name").replace("_", " ").title()
        if value is None:
            raise ValueError(f"{field_label} is required.")
        if not isinstance(value, str):
            raise ValueError(f"{field_label} must be a string.")

        trimmed = value.strip()
        if len(trimmed) < 2:
            raise ValueError(f"{field_label} must contain at least 2 characters after trimming whitespace.")

        if trimmed.isdigit() or not any(c.isalpha() for c in trimmed):
            raise ValueError(f"{field_label} cannot be numeric-only and must contain alphabetic characters.")

        if not NAME_ALLOWED_CHARS.match(trimmed):
            raise ValueError(f"{field_label} contains invalid characters. Only letters, spaces, hyphens, and apostrophes are allowed.")

        return trimmed

    @field_validator("dob", mode="before")
    @classmethod
    def validate_dob(cls, value: Any) -> str:
        if value is None:
            raise ValueError("Date of birth is required.")
        if isinstance(value, date):
            dob_date = value
        elif isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                raise ValueError("Date of birth cannot be empty.")
            try:
                dob_date = date.fromisoformat(trimmed)
            except ValueError:
                raise ValueError("Date of birth must be a valid calendar date in YYYY-MM-DD format.")
        else:
            raise ValueError("Date of birth must be a valid date in YYYY-MM-DD format.")

        today = date.today()
        if dob_date > today:
            raise ValueError(f"Date of birth cannot be in the future (received {dob_date.isoformat()}, today is {today.isoformat()}).")

        if dob_date < date(1900, 1, 1):
            raise ValueError("Date of birth must be on or after 1900-01-01.")

        return dob_date.isoformat()

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value: Any) -> str:
        if value is None:
            raise ValueError("Gender is required.")
        if not isinstance(value, str):
            raise ValueError("Gender must be a string.")

        trimmed = value.strip().capitalize()
        if trimmed not in VALID_GENDERS:
            opts = ", ".join(sorted(VALID_GENDERS))
            raise ValueError(f"Invalid gender '{value}'. Supported options: {opts}.")
        return trimmed

    @field_validator("blood_group", mode="before")
    @classmethod
    def validate_blood_group(cls, value: Any) -> str:
        if value is None:
            raise ValueError("Blood group is required.")
        if not isinstance(value, str):
            raise ValueError("Blood group must be a string.")

        trimmed = value.strip().upper()
        if trimmed not in VALID_BLOOD_GROUPS:
            opts = ", ".join(sorted(VALID_BLOOD_GROUPS))
            raise ValueError(f"Invalid blood group '{value}'. Supported options: {opts}.")
        return trimmed

    @field_validator("contact_phone", mode="before")
    @classmethod
    def validate_phone(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Contact phone must be a string.")

        trimmed = value.strip()
        if not trimmed:
            return None

        digits_count = sum(1 for c in trimmed if c.isdigit())
        if not PHONE_REGEX.match(trimmed) or digits_count < 7 or digits_count > 15:
            raise ValueError(
                f"Contact phone '{value}' is invalid. Must be a valid phone number with 7 to 15 digits (e.g., +1-555-0199, +44 20 7946 0950)."
            )
        return trimmed

    @field_validator("emergency_contact", mode="before")
    @classmethod
    def validate_emergency_contact(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Emergency contact must be a string.")

        trimmed = value.strip()
        if not trimmed:
            return None

        if len(trimmed) < 2:
            raise ValueError("Emergency contact must contain at least 2 characters.")

        if not any(c.isalpha() for c in trimmed):
            raise ValueError("Emergency contact must include a valid contact person name.")

        # If phone number is included in parentheses, e.g. "Jane Doe (+1-555-0198)"
        phone_match = re.search(r"\(([^)]+)\)", trimmed)
        if phone_match:
            embedded_phone = phone_match.group(1).strip()
            digits = sum(1 for c in embedded_phone if c.isdigit())
            if digits > 0 or any(c.isdigit() for c in embedded_phone):
                if not PHONE_REGEX.match(embedded_phone) or digits < 7 or digits > 15:
                    raise ValueError(
                        f"Emergency contact phone number '{embedded_phone}' is invalid. Must contain 7 to 15 digits."
                    )
        else:
            # Check for trailing or separated phone number patterns like "Jane Doe - +1-555-0198"
            digit_runs = re.findall(r"\+?[0-9\-\.\s\(\)]{7,}", trimmed)
            for run in digit_runs:
                clean_run = run.strip()
                digits = sum(1 for c in clean_run if c.isdigit())
                if digits >= 5:
                    if digits < 7 or digits > 15 or not PHONE_REGEX.match(clean_run):
                        raise ValueError(
                            f"Emergency contact phone number '{clean_run}' is invalid. Must contain 7 to 15 digits."
                        )

        return trimmed


class PatientCreate(PatientBase):
    patient_id: Optional[str] = Field(None, description="Optional custom patient_id (auto-generated if omitted)", example="P1001")
    emergency_contact: str = Field(..., description="Meaningful emergency contact person and optional phone", example="Jane Doe (+1-555-0198)")

    @field_validator("emergency_contact", mode="before")
    @classmethod
    def require_emergency_contact(cls, value: Any) -> str:
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError("Emergency contact is required.")
        val = PatientBase.validate_emergency_contact(value)
        if not val:
            raise ValueError("Emergency contact is required.")
        return val


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    contact_phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def validate_update_name(cls, value: Any, info: ValidationInfo) -> Optional[str]:
        if value is None:
            return None
        return PatientBase.validate_name(value, info)

    @field_validator("blood_group", mode="before")
    @classmethod
    def validate_update_blood_group(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        return PatientBase.validate_blood_group(value)

    @field_validator("contact_phone", mode="before")
    @classmethod
    def validate_update_phone(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        return PatientBase.validate_phone(value)

    @field_validator("emergency_contact", mode="before")
    @classmethod
    def validate_update_emergency_contact(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        return PatientBase.validate_emergency_contact(value)


class PatientResponse(PatientBase):
    patient_id: str = Field(..., example="P1001")
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PatientListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[PatientResponse]
