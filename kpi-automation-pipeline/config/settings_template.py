# Important configuration template
# Replace the placeholder values with your actual data.

SERVICE_ACCOUNT_FILE = "service_account.json"

GSHEET = {
    "tracker": {
        "url": "TYPE_YOUR_GSHEET_URL",
        "sheet_id": "TYPE_YOUR_SHEET_ID",
        "tabs": {
            "raw_data_compile": "TYPE_YOUR_TAB_NAME",
            "movement_volume": "TYPE_YOUR_TAB_NAME",
            "recipients": "TYPE_YOUR_TAB_NAME",
        },
    },
    "additional_sheet": {
        "url": "TYPE_YOUR_GSHEET_URL",
        "sheet_id": "TYPE_YOUR_SHEET_ID",
        "tabs": {
            "main": "TYPE_YOUR_TAB_NAME",
        },
        "columns": {
            "id": "TYPE_YOUR_COLUMN_NAME",
            "category": "TYPE_YOUR_COLUMN_NAME",
        },
    },
    "key_shipper": {
        "url": "TYPE_YOUR_GSHEET_URL",
        "sheet_id": "TYPE_YOUR_SHEET_ID",
        "tabs": {
            "main": "TYPE_YOUR_TAB_NAME",
        },
        "clear_range": "A2:B",
        "start_cell": "A2",
    },
    "config": {
        "sheet_id": "TYPE_YOUR_SHEET_ID",
        "tabs": {
            "main": "TYPE_YOUR_TAB_NAME",
        },
        "token_cell": "TYPE_YOUR_CELL",
    },
}

METABASE_CONFIG = {
    "lh": {
        "iv_poa": {
            "url": "TYPE_YOUR_METABASE_URL",
            "report_type": "lh",
            "common_params_template": [
                {
                    "id": "TYPE_YOUR_PARAM_ID",
                    "type": "date/single",
                    "value": "end_date",
                    "target": ["variable", ["template-tag", "TYPE_YOUR_TAG"]],
                }
            ],
            "shipper_params_template": {
                "TYPE_YOUR_SHIPPER_KEY": [
                    {
                        "id": "TYPE_YOUR_PARAM_ID",
                        "type": "string/=",
                        "value": "TYPE_YOUR_VALUE",
                        "target": ["dimension", ["template-tag", "TYPE_YOUR_TAG"]],
                    }
                ]
            },
        }
    }
}

SCHEDULE_DAYS = [1, 2, 6, 10, 14, 15, 16]
