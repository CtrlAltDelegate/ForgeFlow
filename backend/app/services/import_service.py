"""
CSV import: parse, validate, create products + research_data, log to imports.
"""

import csv
import io
from dataclasses import dataclass, field

from app.models import Product, ResearchData, ImportRecord
from app.models.product import ProductStatus, slugify


# Expected CSV columns (flexible: name and category required)
REQUIRED_COLUMNS = {"name", "category"}
OPTIONAL_COLUMNS = {
    "source", "source_keyword", "source_notes",
    "listed_price", "review_count", "rating", "estimated_sales",
    "competitor_count", "listing_count", "listing_age_days", "notes",
}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS


@dataclass
class RowError:
    row: int
    message: str


@dataclass
class ParsedRow:
    name: str
    category: str
    source: str = "csv"
    source_keyword: str | None = None
    source_notes: str | None = None
    listed_price: float | None = None
    review_count: int | None = None
    rating: float | None = None
    estimated_sales: int | None = None
    competitor_count: int | None = None
    listing_count: int | None = None
    listing_age_days: int | None = None
    notes: str | None = None


@dataclass
class ImportResult:
    record_count: int = 0
    created_count: int = 0
    errors: list[RowError] = field(default_factory=list)
    import_id: int | None = None


def _normalize_header(h: str) -> str:
    return h.strip().lower().replace(" ", "_").replace("-", "_")


def _parse_value(key: str, value: str) -> str | float | int | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    value = value.strip()
    if key in ("listed_price", "rating"):
        try:
            return float(value)
        except ValueError:
            return None
    if key in ("review_count", "estimated_sales", "competitor_count", "listing_count", "listing_age_days"):
        try:
            return int(float(value))
        except ValueError:
            return None
    return value


def parse_csv(content: str | bytes) -> tuple[list[ParsedRow], list[RowError]]:
    """
    Parse CSV content. First row = headers.
    Returns (list of parsed rows, list of row errors).
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    rows: list[ParsedRow] = []
    errors: list[RowError] = []

    reader = csv.DictReader(io.StringIO(content))
    raw_headers = reader.fieldnames or []
    headers = {_normalize_header(h): h for h in raw_headers}

    missing = REQUIRED_COLUMNS - set(headers.keys())
    if missing:
        errors.append(RowError(row=0, message=f"Missing required columns: {missing}"))
        return rows, errors

    for i, raw_row in enumerate(reader):
        row_num = i + 2  # 1-based, +1 for header
        row_dict = {_normalize_header(k): v for k, v in raw_row.items() if k}
        name = (row_dict.get("name") or "").strip()
        category = (row_dict.get("category") or "").strip()
        if not name:
            errors.append(RowError(row=row_num, message="Missing product name"))
            continue
        if not category:
            errors.append(RowError(row=row_num, message="Missing category"))
            continue

        try:
            listed_price = _parse_value("listed_price", row_dict.get("listed_price", ""))
            review_count = _parse_value("review_count", row_dict.get("review_count", ""))
            rating = _parse_value("rating", row_dict.get("rating", ""))
            estimated_sales = _parse_value("estimated_sales", row_dict.get("estimated_sales", ""))
            competitor_count = _parse_value("competitor_count", row_dict.get("competitor_count", ""))
            listing_count = _parse_value("listing_count", row_dict.get("listing_count", ""))
            listing_age_days = _parse_value("listing_age_days", row_dict.get("listing_age_days", ""))
        except (TypeError, ValueError) as e:
            errors.append(RowError(row=row_num, message=str(e)))
            continue

        rows.append(ParsedRow(
            name=name,
            category=category,
            source=row_dict.get("source", "csv").strip() or "csv",
            source_keyword=(row_dict.get("source_keyword") or "").strip() or None,
            source_notes=(row_dict.get("source_notes") or "").strip() or None,
            listed_price=float(listed_price) if listed_price is not None else None,
            review_count=int(review_count) if review_count is not None else None,
            rating=float(rating) if rating is not None else None,
            estimated_sales=int(estimated_sales) if estimated_sales is not None else None,
            competitor_count=int(competitor_count) if competitor_count is not None else None,
            listing_count=int(listing_count) if listing_count is not None else None,
            listing_age_days=int(listing_age_days) if listing_age_days is not None else None,
            notes=(row_dict.get("notes") or "").strip() or None,
        ))

    return rows, errors


def get_csv_template() -> str:
    """Return CSV template as string (header + one example row)."""
    headers = [
        "name", "category", "source", "source_keyword", "source_notes",
        "listed_price", "review_count", "rating", "estimated_sales",
        "competitor_count", "listing_count", "listing_age_days", "notes",
    ]
    example = [
        "Desk Cable Clip", "cable organizers", "csv", "desk cable",
        "", "12.99", "150", "4.3", "300", "25", "60", "90", "",
    ]
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(headers)
    w.writerow(example)
    return out.getvalue()
