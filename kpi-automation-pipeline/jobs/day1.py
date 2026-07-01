# ============================================================
# jobs/day1.py - Day 1 Cleansing Last Mile Trackers
# ============================================================

import time
from gspread.exceptions import APIError

from config.settings import GSHEET
from utils.gsheet import clear_range


TRACKER_KEYS = [
    "tracker_gj",
    "tracker_sum",
    "tracker_wj",
    "tracker_cj",
    "tracker_ej",
]


def _iter_ranges(value):
    if isinstance(value, dict):
        return list(value.values())

    if isinstance(value, (list, tuple)):
        return list(value)

    if isinstance(value, str):
        return [value]

    return []


def safe_clear(sheet_id, tracker_key, tab_name, range_a1, max_retry=5):
    for attempt in range(1, max_retry + 1):
        try:
            print(f"  -> [{tracker_key}] Clear {tab_name} | {range_a1}")

            clear_range(
                spreadsheet_id=sheet_id,
                sheet_name=tab_name,
                range_a1=range_a1,
            )

            print("     [SUCCESS]")
            time.sleep(2)
            return True

        except APIError as e:
            err_msg = str(e)
            print(f"     [FAILED attempt {attempt}/{max_retry}] {err_msg}")

            if "429" in err_msg or "Quota exceeded" in err_msg:
                sleep_seconds = attempt * 15
                print(f"     Quota kena. Sleep {sleep_seconds} detik dulu...")
                time.sleep(sleep_seconds)
                continue

            return False

        except Exception as e:
            print(f"     [FAILED attempt {attempt}/{max_retry}] {e}")
            return False

    print(f"     [FAILED FINAL] {tracker_key} | {tab_name} | {range_a1}")
    return False


def clear_one_tracker(tracker_key):
    tracker_conf = GSHEET.get(tracker_key)

    if not tracker_conf:
        print(f"\n[SKIPPED] Config tidak ditemukan: {tracker_key}")
        return {"success": 0, "failed": 0, "skipped": 1}

    sheet_id = tracker_conf["sheet_id"]
    tabs = tracker_conf.get("tabs", {})
    clear_ranges = tracker_conf.get("clear_ranges", {})

    print(f"\n=== CLEAR TRACKER: {tracker_key} ===")

    success = 0
    failed = 0
    skipped = 0

    for tab_key, ranges in clear_ranges.items():
        tab_name = tabs.get(tab_key)

        if not tab_name:
            print(f"  [SKIPPED] Tab key tidak ada di tabs config: {tab_key}")
            skipped += 1
            continue

        for range_a1 in _iter_ranges(ranges):
            ok = safe_clear(
                sheet_id=sheet_id,
                tracker_key=tracker_key,
                tab_name=tab_name,
                range_a1=range_a1,
            )

            if ok:
                success += 1
            else:
                failed += 1

    return {"success": success, "failed": failed, "skipped": skipped}


def run():
    print("\n=== DAY 1 - CLEANSING LAST MILE TRACKERS ===")

    total_success = 0
    total_failed = 0
    total_skipped = 0

    for tracker_key in TRACKER_KEYS:
        result = clear_one_tracker(tracker_key)

        total_success += result["success"]
        total_failed += result["failed"]
        total_skipped += result["skipped"]

        time.sleep(5)

    print("\n=== DAY 1 SUMMARY ===")
    print(f"SUCCESS : {total_success}")
    print(f"FAILED  : {total_failed}")
    print(f"SKIPPED : {total_skipped}")
    print("\n=== DAY 1 SELESAI ===")


if __name__ == "__main__":
    run()
