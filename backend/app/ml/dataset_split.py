
import math
import random
from collections import defaultdict

from backend.app.ml.training_dataset import (
    PatientHistory,
    build_training_dataset,
)
from backend.app.ml.readmission_labels import (
    calculate_readmission_label,
)


def split_patient_histories(
    histories: list[PatientHistory],
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[list[dict], list[dict]]:
    """
    Split labeled patient histories into train/test sets.

    All encounters belonging to one patient stay
    in the same split.

    Returns:
        (train_dataset, test_dataset)
    """

    if not 0 < test_size < 1:
        raise ValueError(
            "test_size must be between 0 and 1."
        )

    grouped_histories = defaultdict(list)

    for history in histories:
        if not history.patient_id.strip():
            raise ValueError(
                "Patient ID cannot be empty."
            )

        label = calculate_readmission_label(
            discharge_date=history.discharge_date,
            subsequent_admission_dates=(
                history.subsequent_admission_dates
            ),
            observation_end_date=history.observation_end_date,
        )

        # Exclude incomplete follow-up.
        if label is None:
            continue

        grouped_histories[history.patient_id].append(
            history
        )

    patient_ids = sorted(grouped_histories.keys())

    if len(patient_ids) < 2:
        raise ValueError(
            "At least two patients with complete "
            "follow-up are required."
        )

    rng = random.Random(random_state)
    rng.shuffle(patient_ids)

    test_count = max(
        1,
        min(
            len(patient_ids) - 1,
            math.ceil(len(patient_ids) * test_size),
        ),
    )

    test_patient_ids = set(
        patient_ids[:test_count]
    )

    train_histories = []
    test_histories = []

    for patient_id, patient_records in (
        grouped_histories.items()
    ):
        if patient_id in test_patient_ids:
            test_histories.extend(patient_records)
        else:
            train_histories.extend(patient_records)

    train_dataset = build_training_dataset(
        train_histories
    )

    test_dataset = build_training_dataset(
        test_histories
    )

    return train_dataset, test_dataset
