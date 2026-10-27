
import csv
import io
from dataclasses import dataclass

from pydantic import ValidationError

from backend.app.schemas.encounter_import import EncounterImportRow


MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 5000

REQUIRED_COLUMNS = {
    "source_record_id",
    "admission_date",
    "discharge_date",
    "encounter_type",
}

ALLOWED_COLUMNS = REQUIRED_COLUMNS | {
    "age",
    "prior_admissions",
    "length_of_stay",
    "diabetes",
}


class CSVImportError(ValueError):
    pass


def parse_encounter_csv(file_content: bytes) -> list[dict]:

    if len(file_content) > MAX_CSV_SIZE_BYTES:
        raise CSVImportError("CSV file exceeds 5 MB limit")

    try:
        text = file_content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CSVImportError(
            "CSV must use UTF-8 encoding"
        ) from exc

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise CSVImportError("CSV file is empty")

    columns = reader.fieldnames

    if len(columns) != len(set(columns)):
        raise CSVImportError(
            "Duplicate CSV columns are not allowed"
        )

    missing = REQUIRED_COLUMNS - set(columns)

    if missing:
        raise CSVImportError(
            f"Missing required columns: {sorted(missing)}"
        )

    unexpected = set(columns) - ALLOWED_COLUMNS

    if unexpected:
        raise CSVImportError(
            f"Unsupported columns: {sorted(unexpected)}"
        )

    rows = []

    for row_number, row in enumerate(reader, start=2):

        if len(rows) >= MAX_CSV_ROWS:
            raise CSVImportError("CSV exceeds 5000 rows")

        # Reject rows with extra or missing columns.
        if None in row or any(
            value is None for value in row.values()
        ):
            raise CSVImportError(
                f"Malformed CSV row at line {row_number}: "
                "column count does not match header"
            )

        rows.append(row)

    if not rows:
        raise CSVImportError("CSV contains no data rows")

    return rows


@dataclass
class CSVValidationResult:
    total_rows: int
    valid_rows: list[EncounterImportRow]
    invalid_rows: list[dict]


def validate_encounter_csv(
    file_content: bytes,
) -> CSVValidationResult:

    raw_rows = parse_encounter_csv(file_content)

    valid_rows = []
    invalid_rows = []
    seen_source_ids = set()

    for row_number, raw_row in enumerate(raw_rows, start=2):

        try:
            validated_row = EncounterImportRow.model_validate(
                raw_row
            )

            source_id = validated_row.source_record_id

            if source_id in seen_source_ids:
                invalid_rows.append({
                    "row_number": row_number,
                    "errors": [
                        "Duplicate source_record_id in CSV"
                    ],
                })
                continue

            seen_source_ids.add(source_id)
            valid_rows.append(validated_row)

        except ValidationError as exc:
            invalid_rows.append({
                "row_number": row_number,
                "errors": [
                    {
                        "field": ".".join(
                            str(part) for part in error["loc"]
                        ),
                        "message": error["msg"],
                    }
                    for error in exc.errors()
                ],
            })

    return CSVValidationResult(
        total_rows=len(raw_rows),
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
    )
