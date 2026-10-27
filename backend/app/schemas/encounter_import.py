
from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class EncounterImportRow(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    source_record_id: str = Field(
        min_length=1,
        max_length=200,
    )

    admission_date: date | None = None
    discharge_date: date | None = None

    encounter_type: str | None = Field(
        default=None,
        max_length=50,
    )

    age: int | None = Field(
        default=None,
        ge=0,
        le=120,
    )

    prior_admissions: int | None = Field(
        default=None,
        ge=0,
    )

    length_of_stay: int | None = Field(
        default=None,
        ge=0,
    )

    diabetes: bool | None = None

    @field_validator(
        "admission_date",
        "discharge_date",
        "age",
        "prior_admissions",
        "length_of_stay",
        "diabetes",
        "encounter_type",
        mode="before",
    )
    @classmethod
    def convert_empty_to_none(cls, value):
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def validate_date_order(self):
        if (
            self.admission_date is not None
            and self.discharge_date is not None
            and self.discharge_date < self.admission_date
        ):
            raise ValueError(
                "discharge_date cannot be before admission_date"
            )

        return self
