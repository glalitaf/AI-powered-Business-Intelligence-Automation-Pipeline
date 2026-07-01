"""Convert the Summary sheet into a long-format report and archive the results."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from gspread.exceptions import WorksheetNotFound

from utils.gsheet import open_by_key

METRIC_PAIRS = [
    ("POA - IV B2B All & B2C Cold", "Tier"),
    ("POA - IV Keyshipper", "Tier"),
    ("POA - IV Others", "Tier"),
    ("LnD Rate B2B All & B2C Cold", "Tier"),
    ("LnD Rate Keyshipper", "Tier"),
    ("LnD Rate Others", "Tier"),
    ("DWS", "Tier"),
]

OUTPUT_HEADERS = ["Month", "Hub", "Metric", "Value", "Tier"]
ARCHIVE_HEADERS = OUTPUT_HEADERS + ["Archived At"]


def convert_summary_to_long_format(
    spreadsheet_id: str,
    source_sheet: str = "Summary",
    output_sheet: str = "Long Format",
    archive_sheet: str = "Long_Format_Archive",
) -> int:
    workbook = open_by_key(spreadsheet_id)

    source_worksheet = workbook.worksheet(source_sheet)
    output_worksheet = get_or_create_worksheet(workbook, output_sheet)
    archive_worksheet = get_or_create_worksheet(workbook, archive_sheet, header=ARCHIVE_HEADERS)

    output_worksheet.clear()

    data = source_worksheet.get_all_values()
    if len(data) < 2:
        output_worksheet.update("A1", [OUTPUT_HEADERS])
        return 0

    headers = [str(value).strip() for value in data[0]]
    rows = data[1:]

    hub_col = _get_header_index(headers, "Hub")
    tier_indexes = [index for index, header in enumerate(headers) if header == "Tier"]

    month = get_previous_month()
    archived_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    long_rows: List[List[str]] = []
    archive_rows: List[List[str]] = []

    for idx, (metric_name, _) in enumerate(METRIC_PAIRS):
        metric_col = _get_header_index(headers, metric_name, default=None)
        tier_col = tier_indexes[idx] if idx < len(tier_indexes) else None

        if metric_col is None or tier_col is None:
            continue

        for row in rows:
            hub = row[hub_col] if hub_col < len(row) else ""
            value = row[metric_col] if metric_col < len(row) else ""
            tier = row[tier_col] if tier_col < len(row) else ""

            if hub and value != "":
                long_rows.append([month, hub, metric_name, value, tier])
                archive_rows.append([month, hub, metric_name, value, tier, archived_at])

    output_values = [OUTPUT_HEADERS] + long_rows
    output_worksheet.update("A1", output_values)

    upsert_archive_rows(archive_worksheet, archive_rows)

    return len(archive_rows)


def get_or_create_worksheet(workbook, title: str, header: Optional[List[str]] = None):
    try:
        worksheet = workbook.worksheet(title)
    except WorksheetNotFound:
        worksheet = workbook.add_worksheet(title=title, rows=1000, cols=max(len(header or OUTPUT_HEADERS), 5))

    if header is not None:
        existing_header = worksheet.row_values(1)
        if existing_header != header:
            worksheet.update("A1", [header])

    return worksheet


def upsert_archive_rows(archive_worksheet, new_rows: List[List[str]]) -> None:
    if not new_rows:
        return

    existing_data = archive_worksheet.get_all_values()
    existing_keys = {
        _archive_key(row): row_index
        for row_index, row in enumerate(existing_data[1:], start=2)
        if len(row) >= 3
    }

    rows_to_append: List[List[str]] = []

    for row in new_rows:
        key = _archive_key(row)
        if key in existing_keys:
            archive_worksheet.update(f"A{existing_keys[key]}", [row])
        else:
            rows_to_append.append(row)

    if rows_to_append:
        start_row = len(existing_data) + 1 if existing_data else 1
        archive_worksheet.update(f"A{start_row}", rows_to_append)


def _archive_key(row: List[str]) -> str:
    return "|".join(str(value).strip() for value in row[:3])


def _get_header_index(headers: List[str], header_name: str, default: Optional[int] = -1) -> Optional[int]:
    try:
        return headers.index(header_name)
    except ValueError:
        return default


def get_previous_month() -> str:
    today = datetime.today()
    year = today.year if today.month > 1 else today.year - 1
    month = today.month - 1 if today.month > 1 else 12
    return f"{year}-{month:02d}"
