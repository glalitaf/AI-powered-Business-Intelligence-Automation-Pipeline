"""Generate MoM comparison from the Long_Format_Archive sheet."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from gspread.exceptions import WorksheetNotFound

from utils.gsheet import open_by_key

OUTPUT_HEADERS = [
    "Previous Month",
    "Current Month",
    "Hub",
    "Metric",
    "Previous Value",
    "Current Value",
    "Delta",
    "Delta Abs",
    "Previous Tier",
    "Current Tier",
    "Tier Movement",
    "Flag",
    "Anomaly Type",
    "Severity",
    "Needs AI Insight",
]


def generate_mom_comparison(
    spreadsheet_id: str,
    archive_sheet_name: str = "Long_Format_Archive",
    output_sheet_name: str = "MoM_Comparison",
) -> int:
    workbook = open_by_key(spreadsheet_id)

    archive_sheet = workbook.worksheet(archive_sheet_name)
    output_sheet = get_or_create_worksheet(workbook, output_sheet_name)
    output_sheet.clear()

    data = archive_sheet.get_all_values()
    if len(data) < 2:
        output_sheet.update("A1", [["Need at least 2 months in Long_Format_Archive"]])
        return 0

    headers = [str(value).strip() for value in data[0]]
    rows = data[1:]

    month_col = _get_header_index(headers, "Month")
    hub_col = _get_header_index(headers, "Hub")
    metric_col = _get_header_index(headers, "Metric")
    value_col = _get_header_index(headers, "Value")
    tier_col = _get_header_index(headers, "Tier")

    months = sorted({row[month_col] for row in rows if len(row) > month_col and row[month_col]})

    if len(months) < 2:
        output_sheet.update("A1", [["Need at least 2 months in Long_Format_Archive"]])
        return 0

    previous_month = months[-2]
    current_month = months[-1]

    previous_map: Dict[str, Dict[str, Any]] = {}
    current_map: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        if len(row) <= metric_col or len(row) <= hub_col:
            continue

        month = row[month_col] if len(row) > month_col else ""
        hub = row[hub_col] if len(row) > hub_col else ""
        metric = row[metric_col] if len(row) > metric_col else ""
        value = parse_percent_or_number(row[value_col] if len(row) > value_col else "")
        tier = row[tier_col] if len(row) > tier_col else ""

        if not hub or not metric or month not in {previous_month, current_month}:
            continue

        key = f"{hub}|{metric}"
        entry = {"value": value, "tier": tier}

        if month == previous_month:
            previous_map[key] = entry
        elif month == current_month:
            current_map[key] = entry

    output_rows: List[List[Any]] = [OUTPUT_HEADERS]

    for key in sorted(current_map):
        if key not in previous_map:
            continue

        previous_value = previous_map[key]["value"]
        current_value = current_map[key]["value"]

        if previous_value is None or current_value is None:
            continue

        delta = current_value - previous_value
        delta_abs = abs(delta)

        previous_tier = previous_map[key]["tier"]
        current_tier = current_map[key]["tier"]

        tier_movement = get_tier_movement(previous_tier, current_tier)
        flag = get_mom_flag(delta, tier_movement, current_tier)
        anomaly = get_anomaly(delta, tier_movement, current_tier)

        hub, metric = key.split("|", 1)
        output_rows.append([
            previous_month,
            current_month,
            hub,
            metric,
            previous_value,
            current_value,
            delta,
            delta_abs,
            previous_tier,
            current_tier,
            tier_movement,
            flag,
            anomaly["type"],
            anomaly["severity"],
            anomaly["needsAI"],
        ])

    if len(output_rows) == 1:
        output_sheet.update("A1", [["No matching rows found for the latest two months"]])
        return 0

    output_sheet.update("A1", output_rows)
    return len(output_rows) - 1


def get_or_create_worksheet(workbook, title: str):
    try:
        return workbook.worksheet(title)
    except WorksheetNotFound:
        return workbook.add_worksheet(title=title, rows=1000, cols=len(OUTPUT_HEADERS))


def parse_percent_or_number(value: Any) -> Optional[float]:
    if value is None:
        return None

    text = str(value).replace("%", "").replace(",", ".").strip()
    if text == "":
        return None

    try:
        return float(text)
    except ValueError:
        return None


def get_tier_movement(previous_tier: str, current_tier: str) -> str:
    previous = extract_tier_number(previous_tier)
    current = extract_tier_number(current_tier)

    if previous is None or current is None:
        return "Unknown"
    if current > previous:
        return "Improved"
    if current < previous:
        return "Declined"
    return "Stable"


def extract_tier_number(tier: Any) -> Optional[int]:
    if tier is None:
        return None

    match = re.search(r"\d+", str(tier))
    return int(match.group()) if match else None


def get_mom_flag(delta: float, tier_movement: str, current_tier: str) -> str:
    current_tier_num = extract_tier_number(current_tier)
    if current_tier_num == 1:
        return "Critical"
    if tier_movement == "Declined":
        return "Tier Declined"
    if delta <= -5:
        return "Significant Drop"
    if delta >= 5:
        return "Significant Improvement"
    return "Normal"


def get_anomaly(delta: float, tier_movement: str, current_tier: str) -> Dict[str, str]:
    current_tier_num = extract_tier_number(current_tier)

    if current_tier_num == 1:
        return {"type": "Current Tier 1", "severity": "Critical", "needsAI": "Yes"}
    if tier_movement == "Declined":
        return {"type": "Tier Declined", "severity": "High", "needsAI": "Yes"}
    if tier_movement == "Improved":
        return {"type": "Tier Improved", "severity": "Opportunity", "needsAI": "Yes"}
    if delta <= -5:
        return {"type": "Significant Drop", "severity": "High", "needsAI": "Yes"}
    if delta >= 5:
        return {"type": "Significant Improvement", "severity": "Opportunity", "needsAI": "Yes"}

    return {"type": "Normal", "severity": "Low", "needsAI": "No"}
