
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatientCreate(BaseModel):
    patient_number: str = Field(min_length=1, max_length=100)
    full_name: str = Field(min_length=1, max_length=200)
    date_of_birth: date | None = None
    sex_at_birth: str | None = Field(default=None, max_length=30)

    @field_validator("patient_number", "full_name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value

    @field_validator("sex_at_birth")
    @classmethod
    def normalize_sex_at_birth(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()
        if not value:
            return None

        if value not in {"male", "female", "intersex", "unknown"}:
            raise ValueError(
                "Must be male, female, intersex, or unknown"
            )

        return value


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    patient_number: str
    full_name: str
    date_of_birth: date | None
    sex_at_birth: str | None
    is_active: bool
    created_at: datetime

class PatientUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    date_of_birth: date | None = None
    sex_at_birth: str | None = Field(
        default=None,
        max_length=30,
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Full name cannot be blank")

        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future")

        return value

    @field_validator("sex_at_birth")
    @classmethod
    def normalize_sex_at_birth(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()

        if not value:
            return None

        if value not in {"male", "female", "intersex", "unknown"}:
            raise ValueError(
                "Must be male, female, intersex, or unknown"
            )

        return value
