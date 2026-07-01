"""Generate a monthly AI summary from the Performance_Summary sheet."""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from typing import Any, List, Optional

import requests
from gspread.exceptions import WorksheetNotFound

from utils.gsheet import open_by_key

GEMINI_MODELS = [
    "gemini-flash-latest",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
]

OUTPUT_HEADERS = [
    "Generated At",
    "Month",
    "Prompt",
    "AI Summary",
]


def generate_monthly_ai_summary(
    spreadsheet_id: str,
    source_sheet_name: str = "Performance_Summary",
    output_sheet_name: str = "Monthly_AI_Summary",
    api_key: Optional[str] = None,
) -> str:
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY tidak ditemukan. Set env var GEMINI_API_KEY atau kirimkan api_key ke fungsi."
        )

    workbook = open_by_key(spreadsheet_id)
    source_sheet = workbook.worksheet(source_sheet_name)
    output_sheet = get_or_create_worksheet(workbook, output_sheet_name)

    values = output_sheet.get_all_values()
    if not values:
        output_sheet.append_row(OUTPUT_HEADERS, value_input_option="USER_ENTERED")

    performance_text = build_performance_summary_text(source_sheet)
    month = extract_current_month_from_performance_summary(source_sheet)
    prompt = build_monthly_summary_prompt(month, performance_text)
    ai_summary = call_gemini_with_fallback(prompt, api_key)

    output_sheet.append_row(
        [
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            month,
            prompt,
            ai_summary,
        ],
        value_input_option="USER_ENTERED",
    )

    print(f"Monthly AI Summary generated for {month}")
    return ai_summary


def get_or_create_worksheet(workbook, title: str):
    try:
        return workbook.worksheet(title)
    except WorksheetNotFound:
        return workbook.add_worksheet(title=title, rows=1000, cols=len(OUTPUT_HEADERS))


def build_performance_summary_text(sheet) -> str:
    data = sheet.get_all_values()
    lines: List[str] = []

    for row in data:
        row_text = " | ".join(str(cell).strip() for cell in row if str(cell).strip() != "")
        if row_text:
            lines.append(row_text)

    return "\n".join(lines)


def extract_current_month_from_performance_summary(sheet) -> str:
    data = sheet.get_all_values()

    for row in data:
        if len(row) >= 2 and str(row[0]).strip() == "Current Month":
            return str(row[1]).strip()

    return "Unknown Month"


def build_monthly_summary_prompt(month: str, performance_text: str) -> str:
    return f"""
You are a Business Intelligence Manager.

Analyze the following monthly KPI performance summary.

Month: {month}

Performance Summary:
{performance_text}

Please provide:
1. Executive Summary
2. Key Improvements
3. Key Risks
4. Recommended Actions
5. Suggested Focus Areas for Next Month

Rules:
- Do not invent causes that are not supported by the data.
- If root cause is unclear, say that further investigation is required.
- Mention both positive improvements and performance risks.
- Keep the response under 300 words.
- Use concise bullet points.
- Finish with 3 recommended actions only.
"""


def call_gemini_with_fallback(prompt: str, api_key: str) -> str:
    for model in GEMINI_MODELS:
        result = call_gemini_model(prompt, model, api_key)
        if not str(result).startswith("ERROR:"):
            return result

        print(f"Model failed: {model} | {result}")
        time.sleep(3)

    return "ERROR: All Gemini models failed or are currently overloaded."


def call_gemini_model(prompt: str, model: str, api_key: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
        },
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return f"ERROR: {response.status_code} {response.text[:200]}"

        result = response.json()
        if result.get("error"):
            return f"ERROR: {result['error'].get('message', 'Unknown error')}"

        return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "ERROR: No response text")
    except Exception as exc:
        return f"ERROR: {exc}"
