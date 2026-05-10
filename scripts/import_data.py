"""Import mock CSV data into MySQL.

The script is intentionally idempotent: it checks natural keys before each
insert, so running it repeatedly will not create duplicate rows.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from sqlalchemy import text
except ModuleNotFoundError:
    text = None  # type: ignore[assignment]


@dataclass
class ImportStats:
    """Track inserted and skipped rows for one import target."""

    inserted: int = 0
    skipped: int = 0


def read_csv(data_dir: Path, filename: str) -> list[dict[str, str]]:
    """Read a CSV file using utf-8-sig to tolerate Excel-style BOM files."""
    path = data_dir / filename
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def required_value(row: dict[str, str], key: str) -> str:
    """Return a required CSV value after trimming whitespace."""
    value = (row.get(key) or "").strip()
    if not value:
        raise ValueError(f"Missing required value: {key} in row {row}")
    return value


def optional_value(row: dict[str, str], key: str) -> str | None:
    """Return None for empty optional CSV values."""
    value = (row.get(key) or "").strip()
    return value or None


def int_value(row: dict[str, str], key: str) -> int:
    """Parse an integer CSV value."""
    return int(required_value(row, key))


def float_value(row: dict[str, str], key: str) -> float:
    """Parse a numeric CSV value as float."""
    return float(required_value(row, key))


def optional_float_value(row: dict[str, str], key: str) -> float | None:
    """Parse an optional numeric CSV value as float."""
    value = optional_value(row, key)
    return float(value) if value is not None else None


def load_dataset(data_dir: Path) -> dict[str, list[dict[str, str]]]:
    """Load all mock data files into memory."""
    return {
        "schools": read_csv(data_dir, "schools.csv"),
        "majors": read_csv(data_dir, "majors.csv"),
        "score_lines": read_csv(data_dir, "score_lines.csv"),
        "admission_plans": read_csv(data_dir, "admission_plans.csv"),
    }


def validate_dataset(dataset: dict[str, list[dict[str, str]]]) -> None:
    """Validate row counts and foreign-code references before importing."""
    school_codes = {required_value(row, "school_code") for row in dataset["schools"]}
    major_codes = {required_value(row, "major_code") for row in dataset["majors"]}

    for file_key in ("score_lines", "admission_plans"):
        for row in dataset[file_key]:
            school_code = required_value(row, "school_code")
            major_code = required_value(row, "major_code")
            if school_code not in school_codes:
                raise ValueError(f"{file_key} references unknown school_code: {school_code}")
            if major_code not in major_codes:
                raise ValueError(f"{file_key} references unknown major_code: {major_code}")


def require_sqlalchemy() -> None:
    """Raise a helpful error if SQLAlchemy is missing for real imports."""
    if text is None:
        raise RuntimeError("SQLAlchemy is required for MySQL import. Run: pip install -r requirements.txt")


def select_id_by_code(conn: Any, table: str, code_column: str, code: str) -> int | None:
    """Return a row ID by business code."""
    result = conn.execute(
        text(f"SELECT id FROM {table} WHERE {code_column} = :code"),
        {"code": code},
    ).scalar_one_or_none()
    return int(result) if result is not None else None


def load_id_map(conn: Any, table: str, code_column: str) -> dict[str, int]:
    """Load business-code to primary-key mappings."""
    rows = conn.execute(text(f"SELECT id, {code_column} AS code FROM {table}")).mappings()
    return {str(row["code"]): int(row["id"]) for row in rows}


def import_schools(conn: Any, rows: list[dict[str, str]]) -> ImportStats:
    """Import schools and skip existing rows by school_code."""
    stats = ImportStats()
    insert_sql = text(
        """
        INSERT INTO school (
          school_code, name, province, city, school_type, education_level,
          is_985, is_211, is_double_first_class, official_website
        ) VALUES (
          :school_code, :name, :province, :city, :school_type, :education_level,
          :is_985, :is_211, :is_double_first_class, :official_website
        )
        """
    )

    for row in rows:
        school_code = required_value(row, "school_code")
        if select_id_by_code(conn, "school", "school_code", school_code):
            stats.skipped += 1
            continue

        conn.execute(
            insert_sql,
            {
                "school_code": school_code,
                "name": required_value(row, "name"),
                "province": required_value(row, "province"),
                "city": optional_value(row, "city"),
                "school_type": optional_value(row, "school_type"),
                "education_level": optional_value(row, "education_level"),
                "is_985": int_value(row, "is_985"),
                "is_211": int_value(row, "is_211"),
                "is_double_first_class": int_value(row, "is_double_first_class"),
                "official_website": optional_value(row, "official_website"),
            },
        )
        stats.inserted += 1
    return stats


def import_majors(conn: Any, rows: list[dict[str, str]]) -> ImportStats:
    """Import majors and skip existing rows by major_code."""
    stats = ImportStats()
    insert_sql = text(
        """
        INSERT INTO major (major_code, name, category, degree_type)
        VALUES (:major_code, :name, :category, :degree_type)
        """
    )

    for row in rows:
        major_code = required_value(row, "major_code")
        if select_id_by_code(conn, "major", "major_code", major_code):
            stats.skipped += 1
            continue

        conn.execute(
            insert_sql,
            {
                "major_code": major_code,
                "name": required_value(row, "name"),
                "category": optional_value(row, "category"),
                "degree_type": optional_value(row, "degree_type"),
            },
        )
        stats.inserted += 1
    return stats


def import_school_majors(
    conn: Any,
    school_ids: dict[str, int],
    major_ids: dict[str, int],
    rows: list[dict[str, str]],
) -> ImportStats:
    """Create school-major relations inferred from score and plan CSV rows."""
    stats = ImportStats()
    seen_pairs = {
        (required_value(row, "school_code"), required_value(row, "major_code"))
        for row in rows
    }

    exists_sql = text(
        """
        SELECT id FROM school_major
        WHERE school_id = :school_id AND major_id = :major_id
        """
    )
    insert_sql = text(
        """
        INSERT INTO school_major (school_id, major_id, school_major_code, degree_type, duration_years)
        VALUES (:school_id, :major_id, :school_major_code, :degree_type, :duration_years)
        """
    )

    for school_code, major_code in sorted(seen_pairs):
        school_id = school_ids[school_code]
        major_id = major_ids[major_code]
        exists = conn.execute(
            exists_sql,
            {"school_id": school_id, "major_id": major_id},
        ).scalar_one_or_none()
        if exists:
            stats.skipped += 1
            continue

        conn.execute(
            insert_sql,
            {
                "school_id": school_id,
                "major_id": major_id,
                "school_major_code": major_code,
                "degree_type": None,
                "duration_years": None,
            },
        )
        stats.inserted += 1
    return stats


def score_line_exists(
    conn: Any,
    school_id: int,
    major_id: int | None,
    row: dict[str, str],
) -> bool:
    """Check score_line existence by a natural business key."""
    if major_id is None:
        sql = text(
            """
            SELECT id FROM score_line
            WHERE school_id = :school_id
              AND major_id IS NULL
              AND year = :year
              AND province = :province
              AND subject_type = :subject_type
              AND batch = :batch
            """
        )
        params: dict[str, Any] = {"school_id": school_id}
    else:
        sql = text(
            """
            SELECT id FROM score_line
            WHERE school_id = :school_id
              AND major_id = :major_id
              AND year = :year
              AND province = :province
              AND subject_type = :subject_type
              AND batch = :batch
            """
        )
        params = {"school_id": school_id, "major_id": major_id}

    params.update(
        {
            "year": int_value(row, "year"),
            "province": required_value(row, "province"),
            "subject_type": required_value(row, "subject_type"),
            "batch": required_value(row, "batch"),
        }
    )
    return conn.execute(sql, params).scalar_one_or_none() is not None


def import_score_lines(
    conn: Any,
    school_ids: dict[str, int],
    major_ids: dict[str, int],
    rows: list[dict[str, str]],
) -> ImportStats:
    """Import historical score lines and skip existing natural-key rows."""
    stats = ImportStats()
    insert_sql = text(
        """
        INSERT INTO score_line (
          school_id, major_id, year, province, subject_type, batch,
          min_score, min_rank, avg_score, max_score
        ) VALUES (
          :school_id, :major_id, :year, :province, :subject_type, :batch,
          :min_score, :min_rank, :avg_score, :max_score
        )
        """
    )

    for row in rows:
        school_id = school_ids[required_value(row, "school_code")]
        major_code = optional_value(row, "major_code")
        major_id = major_ids[major_code] if major_code else None

        if score_line_exists(conn, school_id, major_id, row):
            stats.skipped += 1
            continue

        conn.execute(
            insert_sql,
            {
                "school_id": school_id,
                "major_id": major_id,
                "year": int_value(row, "year"),
                "province": required_value(row, "province"),
                "subject_type": required_value(row, "subject_type"),
                "batch": required_value(row, "batch"),
                "min_score": int_value(row, "min_score"),
                "min_rank": int_value(row, "min_rank"),
                "avg_score": optional_float_value(row, "avg_score"),
                "max_score": int_value(row, "max_score"),
            },
        )
        stats.inserted += 1
    return stats


def admission_plan_exists(
    conn: Any,
    school_id: int,
    major_id: int,
    row: dict[str, str],
) -> bool:
    """Check admission_plan existence by a natural business key."""
    sql = text(
        """
        SELECT id FROM admission_plan
        WHERE school_id = :school_id
          AND major_id = :major_id
          AND year = :year
          AND province = :province
          AND subject_type = :subject_type
          AND batch = :batch
        """
    )
    return (
        conn.execute(
            sql,
            {
                "school_id": school_id,
                "major_id": major_id,
                "year": int_value(row, "year"),
                "province": required_value(row, "province"),
                "subject_type": required_value(row, "subject_type"),
                "batch": required_value(row, "batch"),
            },
        ).scalar_one_or_none()
        is not None
    )


def import_admission_plans(
    conn: Any,
    school_ids: dict[str, int],
    major_ids: dict[str, int],
    rows: list[dict[str, str]],
) -> ImportStats:
    """Import admission plans and skip existing natural-key rows."""
    stats = ImportStats()
    insert_sql = text(
        """
        INSERT INTO admission_plan (
          school_id, major_id, year, province, subject_type, batch,
          enrollment_count, tuition, duration_years
        ) VALUES (
          :school_id, :major_id, :year, :province, :subject_type, :batch,
          :enrollment_count, :tuition, :duration_years
        )
        """
    )

    for row in rows:
        school_id = school_ids[required_value(row, "school_code")]
        major_id = major_ids[required_value(row, "major_code")]

        if admission_plan_exists(conn, school_id, major_id, row):
            stats.skipped += 1
            continue

        conn.execute(
            insert_sql,
            {
                "school_id": school_id,
                "major_id": major_id,
                "year": int_value(row, "year"),
                "province": required_value(row, "province"),
                "subject_type": required_value(row, "subject_type"),
                "batch": required_value(row, "batch"),
                "enrollment_count": int_value(row, "enrollment_count"),
                "tuition": float_value(row, "tuition"),
                "duration_years": float_value(row, "duration_years"),
            },
        )
        stats.inserted += 1
    return stats


def print_dataset_summary(dataset: dict[str, list[dict[str, str]]]) -> None:
    """Print CSV row counts for dry-run validation."""
    print("CSV validation passed.")
    print(f"schools: {len(dataset['schools'])}")
    print(f"majors: {len(dataset['majors'])}")
    print(f"score_lines: {len(dataset['score_lines'])}")
    print(f"admission_plans: {len(dataset['admission_plans'])}")


def print_import_stats(stats: dict[str, ImportStats]) -> None:
    """Print a compact import report."""
    print("Import finished.")
    for name, item in stats.items():
        print(f"{name}: inserted={item.inserted}, skipped={item.skipped}")


def import_to_mysql(dataset: dict[str, list[dict[str, str]]]) -> dict[str, ImportStats]:
    """Import all CSV data into MySQL inside one transaction."""
    require_sqlalchemy()
    from app.db.database import engine

    with engine.begin() as conn:
        stats = {
            "schools": import_schools(conn, dataset["schools"]),
            "majors": import_majors(conn, dataset["majors"]),
        }
        school_ids = load_id_map(conn, "school", "school_code")
        major_ids = load_id_map(conn, "major", "major_code")

        relation_rows = dataset["score_lines"] + dataset["admission_plans"]
        stats["school_majors"] = import_school_majors(
            conn,
            school_ids,
            major_ids,
            relation_rows,
        )
        stats["score_lines"] = import_score_lines(
            conn,
            school_ids,
            major_ids,
            dataset["score_lines"],
        )
        stats["admission_plans"] = import_admission_plans(
            conn,
            school_ids,
            major_ids,
            dataset["admission_plans"],
        )
    return stats


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="Import mock gaokao data into MySQL.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing schools.csv, majors.csv, score_lines.csv, admission_plans.csv.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV files and print row counts without writing to MySQL.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    dataset = load_dataset(args.data_dir)
    validate_dataset(dataset)

    if args.dry_run:
        print_dataset_summary(dataset)
        return

    stats = import_to_mysql(dataset)
    print_import_stats(stats)


if __name__ == "__main__":
    main()
