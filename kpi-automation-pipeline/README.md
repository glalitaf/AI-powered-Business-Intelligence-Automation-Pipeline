# KPI Automation Pipeline

## Executive Summary
This project is an end-to-end automation pipeline designed to transform fragmented KPI data into reliable, decision-ready reporting for business operations teams. It extracts data from Metabase, applies business rules and transformations, writes structured outputs to Google Sheets, and supports monthly performance reviews with comparison and summary layers.

## Why This Project Matters
In a business environment, KPI reporting is often manual, repetitive, and prone to inconsistency. This pipeline addresses that problem by:
- reducing manual reporting effort,
- standardizing KPI calculations across teams,
- improving visibility into monthly performance changes,
- enabling faster, data-backed operational decisions.

## What the Project Does
The pipeline automates the following workflow:
1. Pull KPI data from internal data sources.
2. Standardize and transform raw metrics into business-ready formats.
3. Write results to structured Google Sheets dashboards.
4. Generate comparison views such as month-over-month analysis.
5. Support performance summary generation for leadership reporting.

## Business Value
- Faster reporting cycle for operations and leadership teams.
- More consistent KPI definitions across dashboards and reviews.
- Reduced risk of human error in manual aggregation.
- Better visibility for performance trends, risks, and improvement areas.
- A scalable foundation for future analytics and AI-assisted insights.

## Key Technical Strengths Demonstrated
- Python-based automation with modular job orchestration.
- Data extraction and transformation using pandas.
- Google Sheets integration for operational reporting workflows.
- Config-driven architecture for maintainability and reuse.
- Clean separation of responsibilities across jobs, utilities, and transformations.

## Tech Stack
- Python
- pandas
- requests
- gspread
- Google Sheets API
- Metabase data integration

## Project Structure
```text
.
├── jobs/                  # Scheduled execution jobs
├── utils/                 # Shared helpers for extraction, transformation, and sheets access
├── config/                # Configuration and environment settings
└── AI_summary/            # Summary and AI-assisted monthly reporting modules
```

## Example Workflow
```bash
python main.py
```

This entry point triggers the configured daily/periodic automation jobs that handle data collection, transformation, and reporting outputs.

## Impact for a Hiring Manager
This project shows practical engineering skills in:
- building reliable automation pipelines,
- working with business data and operational metrics,
- creating maintainable software with reusable components,
- solving real-world reporting inefficiencies with measurable business value.

## Summary
This is not just a data script collection—it is a business-focused automation solution that improves how KPI performance is captured, reviewed, and communicated. It demonstrates both technical execution and an understanding of operational needs, which is valuable for a hiring manager evaluating impact-driven engineering work.

## Future Enhancements
- Add automated scheduler support.
- Improve alerting and exception handling.
- Expand AI-assisted insights for leadership summaries.
- Add monitoring and audit logs for production reliability.
