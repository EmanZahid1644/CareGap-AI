
from dataclasses import dataclass
from datetime import date

from backend.app.ml.readmission_features import ReadmissionFeatures
from backend.app.ml.readmission_labels import (
    calculate_readmission_label,
)


@dataclass(frozen=True)
class PatientHistory:
    """
    Synthetic patient history for ML prototyping.

    Features must be known at discharge.
    Subsequent admissions are used only for labels.
    """

    patient_id: str
    discharge_date: date
    features: ReadmissionFeatures
    subsequent_admission_dates: list[date]
    observation_end_date: date


def build_training_dataset(
    histories: list[PatientHistory],
) -> list[dict]:
    """
    Convert patient histories into labeled ML rows.

    Excludes incomplete follow-up outcomes.
    Does not include patient IDs in training rows.
    """

    dataset = []

    for history in histories:
        label = calculate_readmission_label(
            discharge_date=history.discharge_date,
            subsequent_admission_dates=(
                history.subsequent_admission_dates
            ),
            observation_end_date=history.observation_end_date,
        )

        if label is None:
            continue

        row = history.features.model_dump()
        row["readmitted_30_days"] = label

        dataset.append(row)

    return dataset
