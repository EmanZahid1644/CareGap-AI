
import math
import random
from datetime import date
from pathlib import Path

import joblib

from backend.app.ml.readmission_features import ReadmissionFeatures
from backend.app.ml.training_dataset import PatientHistory
from backend.app.ml.dataset_split import split_patient_histories
from backend.app.ml.model_training import (
    FEATURE_COLUMNS,
    train_readmission_model,
)


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "artifacts"
    / "readmission_demo.joblib"
)


def generate_synthetic_histories(
    count: int = 300,
) -> list[PatientHistory]:
    """
    Generate synthetic patient histories for a
    technical demonstration only.

    These are NOT real clinical outcomes.
    """

    rng = random.Random(42)
    histories = []

    for i in range(count):
        age = rng.randint(18, 90)
        prior_admissions = rng.randint(0, 6)
        length_of_stay = rng.randint(1, 14)
        diabetes = rng.choice([True, False])

        features = ReadmissionFeatures(
            age=age,
            prior_admissions=prior_admissions,
            length_of_stay=length_of_stay,
            diabetes=diabetes,
        )

        # Artificial relationship used only to
        # demonstrate the ML training pipeline.
        logit = (
            -3.5
            + 0.018 * age
            + 0.48 * prior_admissions
            + 0.055 * length_of_stay
            + 0.55 * int(diabetes)
        )

        probability = 1 / (1 + math.exp(-logit))
        readmitted = rng.random() < probability

        histories.append(
            PatientHistory(
                patient_id=f"SYN-{i:05d}",
                discharge_date=date(2026, 10, 1),
                features=features,
                subsequent_admission_dates=(
                    [date(2026, 10, 15)]
                    if readmitted
                    else []
                ),
                observation_end_date=date(2026, 12, 1),
            )
        )

    return histories


def main():
    histories = generate_synthetic_histories()

    train_data, test_data = split_patient_histories(
        histories,
        test_size=0.2,
        random_state=42,
    )

    model, metrics = train_readmission_model(
        train_data,
        test_data,
    )

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        {
            "model": model,
            "feature_columns": FEATURE_COLUMNS,
            "model_version": "demo-1.0",
            "data_source": "synthetic",
        },
        MODEL_PATH,
    )

    print("\nCareGap-AI Demo Model Trained")
    print("-----------------------------")

    for name, value in metrics.items():
        print(f"{name}: {value}")

    print(f"\nModel saved: {MODEL_PATH}")
    print(
        "\nWARNING: Synthetic demonstration model. "
        "Not validated for clinical use."
    )


if __name__ == "__main__":
    main()
