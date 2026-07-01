"""Generate Performance_Summary sheet from MoM_Comparison data."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from gspread.exceptions import WorksheetNotFound

from utils.gsheet import open_by_key


def generate_performance_summary(
    spreadsheet_id: str,
    source_sheet_name: str = "MoM_Comparison",
    output_sheet_name: str = "Performance_Summary",
) -> int:
    workbook = open_by_key(spreadsheet_id)
    source_sheet = workbook.worksheet(source_sheet_name)
    output_sheet = get_or_create_worksheet(workbook, output_sheet_name)

    output_sheet.clear()
    data = source_sheet.get_all_values()
    if len(data) < 2:
        return 0

    headers = [str(value).strip() for value in data[0]]
    rows = data[1:]

    prev_month_col = _get_header_index(headers, "Previous Month")
    curr_month_col = _get_header_index(headers, "Current Month")
    hub_col = _get_header_index(headers, "Hub")
    metric_col = _get_header_index(headers, "Metric")
    prev_value_col = _get_header_index(headers, "Previous Value")
    curr_value_col = _get_header_index(headers, "Current Value")
    delta_col = _get_header_index(headers, "Delta")
    prev_tier_col = _get_header_index(headers, "Previous Tier")
    curr_tier_col = _get_header_index(headers, "Current Tier")
    tier_movement_col = _get_header_index(headers, "Tier Movement")
    anomaly_type_col = _get_header_index(headers, "Anomaly Type")
    severity_col = _get_header_index(headers, "Severity")
    needs_ai_col = _get_header_index(headers, "Needs AI Insight")

    if not rows:
        return 0

    previous_month = rows[0][prev_month_col] if prev_month_col >= 0 and len(rows[0]) > prev_month_col else ""
    current_month = rows[0][curr_month_col] if curr_month_col >= 0 and len(rows[0]) > curr_month_col else ""

    output: List[List[Any]] = []

    # SECTION 1: OVERALL SUMMARY
    total_records = len(rows)
    unique_hubs = len({row[hub_col] for row in rows if hub_col >= 0 and len(row) > hub_col and row[hub_col]})
    unique_metrics = len({row[metric_col] for row in rows if metric_col >= 0 and len(row) > metric_col and row[metric_col]})

    improved_records = sum(1 for row in rows if tier_movement_col >= 0 and len(row) > tier_movement_col and row[tier_movement_col] == "Improved")
    declined_records = sum(1 for row in rows if tier_movement_col >= 0 and len(row) > tier_movement_col and row[tier_movement_col] == "Declined")
    stable_records = sum(1 for row in rows if tier_movement_col >= 0 and len(row) > tier_movement_col and row[tier_movement_col] == "Stable")

    critical_records = sum(1 for row in rows if severity_col >= 0 and len(row) > severity_col and row[severity_col] == "Critical")
    high_records = sum(1 for row in rows if severity_col >= 0 and len(row) > severity_col and row[severity_col] == "High")
    opportunity_records = sum(1 for row in rows if severity_col >= 0 and len(row) > severity_col and row[severity_col] == "Opportunity")
    needs_ai_records = sum(1 for row in rows if needs_ai_col >= 0 and len(row) > needs_ai_col and row[needs_ai_col] == "Yes")

    output.append(["SECTION 1 - OVERALL SUMMARY"])
    output.append(["Item", "Value"])
    output.append(["Previous Month", previous_month])
    output.append(["Current Month", current_month])
    output.append(["Total KPI Records", total_records])
    output.append(["Total Hubs", unique_hubs])
    output.append(["Total Metrics", unique_metrics])
    output.append(["Improved Records", improved_records])
    output.append(["Declined Records", declined_records])
    output.append(["Stable Records", stable_records])
    output.append(["Critical Records", critical_records])
    output.append(["High Risk Records", high_records])
    output.append(["Opportunity Records", opportunity_records])
    output.append(["Needs AI Insight Records", needs_ai_records])
    output.append([""])

    # SECTION 2: KPI MOVEMENT BY METRIC
    metric_summary: Dict[str, Dict[str, int]] = {}
    for row in rows:
        metric = row[metric_col] if metric_col >= 0 and len(row) > metric_col else ""
        movement = row[tier_movement_col] if tier_movement_col >= 0 and len(row) > tier_movement_col else ""
        severity = row[severity_col] if severity_col >= 0 and len(row) > severity_col else ""
        if not metric:
            continue

        summary = metric_summary.setdefault(metric, {
            "improved": 0,
            "declined": 0,
            "stable": 0,
            "critical": 0,
            "high": 0,
            "opportunity": 0,
        })

        if movement == "Improved":
            summary["improved"] += 1
        if movement == "Declined":
            summary["declined"] += 1
        if movement == "Stable":
            summary["stable"] += 1
        if severity == "Critical":
            summary["critical"] += 1
        if severity == "High":
            summary["high"] += 1
        if severity == "Opportunity":
            summary["opportunity"] += 1

    output.append(["SECTION 2 - KPI MOVEMENT BY METRIC"])
    output.append(["Metric", "Improved", "Declined", "Stable", "Critical", "High Risk", "Opportunity"])
    for metric, summary in metric_summary.items():
        output.append([
            metric,
            summary["improved"],
            summary["declined"],
            summary["stable"],
            summary["critical"],
            summary["high"],
            summary["opportunity"],
        ])
    output.append([""])

    # SECTION 3: TIER DISTRIBUTION
    previous_tier_dist: Dict[str, int] = {}
    current_tier_dist: Dict[str, int] = {}

    for row in rows:
        prev_tier = row[prev_tier_col] if prev_tier_col >= 0 and len(row) > prev_tier_col else "Blank"
        curr_tier = row[curr_tier_col] if curr_tier_col >= 0 and len(row) > curr_tier_col else "Blank"
        previous_tier_dist[prev_tier] = previous_tier_dist.get(prev_tier, 0) + 1
        current_tier_dist[curr_tier] = current_tier_dist.get(curr_tier, 0) + 1

    all_tiers = sorted(set(previous_tier_dist) | set(current_tier_dist))
    output.append(["SECTION 3 - TIER DISTRIBUTION"])
    output.append(["Tier", "Previous Month", "Current Month", "Delta"])
    for tier in all_tiers:
        prev = previous_tier_dist.get(tier, 0)
        curr = current_tier_dist.get(tier, 0)
        output.append([tier, prev, curr, curr - prev])
    output.append([""])

    # SECTION 4: TOP 10 IMPROVEMENT
    top_improvement = sorted(
        [
            {
                "hub": row[hub_col] if hub_col >= 0 and len(row) > hub_col else "",
                "metric": row[metric_col] if metric_col >= 0 and len(row) > metric_col else "",
                "previousValue": row[prev_value_col] if prev_value_col >= 0 and len(row) > prev_value_col else "",
                "currentValue": row[curr_value_col] if curr_value_col >= 0 and len(row) > curr_value_col else "",
                "delta": parse_number(row[delta_col] if delta_col >= 0 and len(row) > delta_col else ""),
                "previousTier": row[prev_tier_col] if prev_tier_col >= 0 and len(row) > prev_tier_col else "",
                "currentTier": row[curr_tier_col] if curr_tier_col >= 0 and len(row) > curr_tier_col else "",
                "severity": row[severity_col] if severity_col >= 0 and len(row) > severity_col else "",
            }
            for row in rows
        ],
        key=lambda item: item["delta"],
        reverse=True,
    )

    output.append(["SECTION 4 - TOP 10 IMPROVEMENT"])
    output.append(["Hub", "Metric", "Previous Value", "Current Value", "Delta", "Previous Tier", "Current Tier", "Severity"])
    for row in top_improvement[:10]:
        output.append([
            row["hub"],
            row["metric"],
            row["previousValue"],
            row["currentValue"],
            row["delta"],
            row["previousTier"],
            row["currentTier"],
            row["severity"],
        ])
    output.append([""])

    # SECTION 5: TOP 10 DECLINE
    top_decline = sorted(
        [
            {
                "hub": row[hub_col] if hub_col >= 0 and len(row) > hub_col else "",
                "metric": row[metric_col] if metric_col >= 0 and len(row) > metric_col else "",
                "previousValue": row[prev_value_col] if prev_value_col >= 0 and len(row) > prev_value_col else "",
                "currentValue": row[curr_value_col] if curr_value_col >= 0 and len(row) > curr_value_col else "",
                "delta": parse_number(row[delta_col] if delta_col >= 0 and len(row) > delta_col else ""),
                "previousTier": row[prev_tier_col] if prev_tier_col >= 0 and len(row) > prev_tier_col else "",
                "currentTier": row[curr_tier_col] if curr_tier_col >= 0 and len(row) > curr_tier_col else "",
                "severity": row[severity_col] if severity_col >= 0 and len(row) > severity_col else "",
            }
            for row in rows
        ],
        key=lambda item: item["delta"],
    )

    output.append(["SECTION 5 - TOP 10 DECLINE"])
    output.append(["Hub", "Metric", "Previous Value", "Current Value", "Delta", "Previous Tier", "Current Tier", "Severity"])
    for row in top_decline[:10]:
        output.append([
            row["hub"],
            row["metric"],
            row["previousValue"],
            row["currentValue"],
            row["delta"],
            row["previousTier"],
            row["currentTier"],
            row["severity"],
        ])
    output.append([""])

    # SECTION 6: CRITICAL ITEMS
    critical_items = [
        row
        for row in rows
        if severity_col >= 0 and len(row) > severity_col and row[severity_col] == "Critical"
    ][:20]

    output.append(["SECTION 6 - CRITICAL ITEMS"])
    output.append(["Hub", "Metric", "Previous Value", "Current Value", "Delta", "Previous Tier", "Current Tier", "Anomaly Type"])
    for row in critical_items:
        output.append([
            row[hub_col] if hub_col >= 0 and len(row) > hub_col else "",
            row[metric_col] if metric_col >= 0 and len(row) > metric_col else "",
            row[prev_value_col] if prev_value_col >= 0 and len(row) > prev_value_col else "",
            row[curr_value_col] if curr_value_col >= 0 and len(row) > curr_value_col else "",
            row[delta_col] if delta_col >= 0 and len(row) > delta_col else "",
            row[prev_tier_col] if prev_tier_col >= 0 and len(row) > prev_tier_col else "",
            row[curr_tier_col] if curr_tier_col >= 0 and len(row) > curr_tier_col else "",
            row[anomaly_type_col] if anomaly_type_col >= 0 and len(row) > anomaly_type_col else "",
        ])

    output_sheet.update("A1", pad_rows(output, 8))
    return len(output)


def get_or_create_worksheet(workbook, title: str):
    try:
        return workbook.worksheet(title)
    except WorksheetNotFound:
        return workbook.add_worksheet(title=title, rows=1000, cols=8)


def parse_number(value: Any) -> float:
    if value is None:
        return 0.0

    clean = str(value).replace("%", "").replace(",", ".").strip()
    if clean == "":
        return 0.0

    try:
        return float(clean)
    except ValueError:
        return 0.0


def _get_header_index(headers: List[str], header_name: str) -> int:
    try:
        return headers.index(header_name)
    except ValueError:
        return -1


def pad_rows(rows: List[List[Any]], width: int) -> List[List[Any]]:
    result: List[List[Any]] = []
    for row in rows:
        new_row = list(row)
        while len(new_row) < width:
            new_row.append("")
        result.append(new_row)
    return result
