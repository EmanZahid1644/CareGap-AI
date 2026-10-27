
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.app.ml.dataset_validation import (
    validate_training_dataset,
)


FEATURE_COLUMNS = [
    "age",
    "prior_admissions",
    "length_of_stay",
    "diabetes",
]

TARGET_COLUMN = "readmitted_30_days"


def prepare_features(dataset: list[dict]) -> list[list[float]]:
    """
    Convert validated ML rows into numeric features.
    """

    return [
        [
            float(row["age"]),
            float(row["prior_admissions"]),
            float(row["length_of_stay"]),
            float(row["diabetes"]),
        ]
        for row in dataset
    ]


def train_readmission_model(
    train_dataset: list[dict],
    test_dataset: list[dict],
) -> tuple[Pipeline, dict]:
    """
    Train and evaluate a baseline Logistic Regression model.

    Both datasets must contain positive and negative
    readmission examples.

    Returns:
        trained model
        evaluation metrics
    """

    # -----------------------------------------
    # 1. Validate datasets
    # -----------------------------------------

    train_stats = validate_training_dataset(
        train_dataset
    )

    test_stats = validate_training_dataset(
        test_dataset
    )

    # -----------------------------------------
    # 2. Prepare features and labels
    # -----------------------------------------

    X_train = prepare_features(train_dataset)

    y_train = [
        row[TARGET_COLUMN]
        for row in train_dataset
    ]

    X_test = prepare_features(test_dataset)

    y_test = [
        row[TARGET_COLUMN]
        for row in test_dataset
    ]

    # -----------------------------------------
    # 3. Build model pipeline
    # -----------------------------------------

    model = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )

    # -----------------------------------------
    # 4. Train model
    # -----------------------------------------

    model.fit(X_train, y_train)

    # -----------------------------------------
    # 5. Generate predictions
    # -----------------------------------------

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    # -----------------------------------------
    # 6. Evaluate model
    # -----------------------------------------

    metrics = {
        "training_samples": train_stats["total_rows"],
        "testing_samples": test_stats["total_rows"],

        "accuracy": round(
            accuracy_score(y_test, predictions),
            4,
        ),

        "precision": round(
            precision_score(
                y_test,
                predictions,
                zero_division=0,
            ),
            4,
        ),

        "recall": round(
            recall_score(
                y_test,
                predictions,
                zero_division=0,
            ),
            4,
        ),

        "roc_auc": round(
            roc_auc_score(
                y_test,
                probabilities,
            ),
            4,
        ),

        "brier_score": round(
            brier_score_loss(
                y_test,
                probabilities,
            ),
            4,
        ),
    }

    return model, metrics
