
from pydantic import BaseModel, Field, ConfigDict


class ReadmissionFeatures(BaseModel):
    """
    Features available at hospital discharge.

    These inputs will be used by the future
    30-day readmission risk prediction model.
    """

    model_config = ConfigDict(extra="forbid")

    age: int = Field(
        ge=0,
        le=120,
        description="Patient age in years",
    )

    prior_admissions: int = Field(
        ge=0,
        description="Previous admissions in the defined lookback period",
    )

    length_of_stay: int = Field(
        ge=0,
        description="Hospital stay duration in days",
    )

    diabetes: bool = Field(
        description="Whether the patient has diabetes",
    )
