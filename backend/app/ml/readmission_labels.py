
from datetime import date, timedelta


def calculate_readmission_label(
    discharge_date: date,
    subsequent_admission_dates: list[date],
    observation_end_date: date,
) -> int | None:
    """
    Determine the 30-day readmission outcome.

    Returns:
        1: Readmission occurred within 30 days.
        0: No readmission, with complete follow-up.
        None: Follow-up is incomplete.

    Assumptions:
        - Admission dates belong to the same patient.
        - Dates are from a complete, reliable data source.
        - All supplied subsequent admissions are relevant
          to the chosen readmission outcome definition.
    """

    if observation_end_date < discharge_date:
        raise ValueError(
            "Observation end date cannot precede discharge date."
        )

    follow_up_end = discharge_date + timedelta(days=30)

    for admission_date in subsequent_admission_dates:
        if discharge_date < admission_date <= follow_up_end:
            if admission_date <= observation_end_date:
                return 1

    if observation_end_date >= follow_up_end:
        return 0

    return None
