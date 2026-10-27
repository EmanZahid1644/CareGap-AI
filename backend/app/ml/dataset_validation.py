
from collections import Counter

from pydantic import ValidationError

from backend.app.ml.readmission_features import (
    ReadmissionFeatures,
)


def validate_training_dataset(
    dataset: list[dict],
) -> dict:
    """
    Validate a labeled readmission training dataset.

    Returns dataset statistics when valid.
    Raises ValueError for invalid datasets.
    """

    if not dataset:
        raise ValueError(
            "Training dataset cannot be empty."
        )

    labels = []

    for index, row in enumerate(dataset, start=1):

        if not isinstance(row, dict):
            raise ValueError(
                f"Row {index}: expected a dictionary."
            )

        label = row.get("readmitted_30_days")

        if type(label) is not int or label not in (0, 1):
            raise ValueError(
                f"Row {index}: invalid readmission label."
            )

        features = {
            key: value
            for key, value in row.items()
            if key != "readmitted_30_days"
        }

        try:
            ReadmissionFeatures.model_validate(
                features
            )
        except ValidationError as exc:
            raise ValueError(
                f"Row {index}: invalid ML features."
            ) from exc

        labels.append(label)

    counts = Counter(labels)

    if len(counts) < 2:
        raise ValueError(
            "Training dataset must contain both "
            "readmitted and non-readmitted examples."
        )

    return {
        "total_rows": len(dataset),
        "positive_cases": counts[1],
        "negative_cases": counts[0],
        "positive_rate": round(
            counts[1] / len(dataset),
            4,
        ),
    }
