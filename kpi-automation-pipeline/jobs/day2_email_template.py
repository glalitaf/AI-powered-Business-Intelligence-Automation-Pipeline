from __future__ import annotations

import re
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import GSHEET
from utils.gsheet import get_cell_value, read_sheet


SENDER_DISPLAY_NAME = "TYPE_YOUR_SENDER_DISPLAY_NAME"
SENDER_ALIAS_EMAIL = "TYPE_YOUR_SENDER_EMAIL"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


# =========================
# SENSITIVE LINKS / FORMS
# =========================
SANGGAHAN_XCLD_URL = "TYPE_YOUR_XCLD_FORM_URL"
SANGGAHAN_NON_XCLD_URL = "TYPE_YOUR_NON_XCLD_FORM_URL"
SANGGAHAN_CLUSTER_URL = "TYPE_YOUR_CLUSTER_FORM_URL"


EMAIL_JOBS = [
    {
        "area_label": "TYPE_YOUR_AREA_NAME",
        "to_tab_key": "TYPE_YOUR_TO_TAB_KEY",
        "sosialisasi_url": "TYPE_YOUR_SOCIALIZATION_LINK",
        "tracker_links": [
            ("TYPE_YOUR_TRACKER_LABEL", "TYPE_YOUR_GSHEET_KEY"),
        ],
    },
    {
        "area_label": "TYPE_YOUR_AREA_NAME",
        "to_tab_key": "TYPE_YOUR_TO_TAB_KEY",
        "sosialisasi_url": "TYPE_YOUR_SOCIALIZATION_LINK",
        "tracker_links": [
            ("TYPE_YOUR_TRACKER_LABEL", "TYPE_YOUR_GSHEET_KEY"),
        ],
    },
]


def get_previous_month_label() -> str:
    months_id = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]

    prev_month_date = datetime.today().replace(day=1) - timedelta(days=1)

    return f"{months_id[prev_month_date.month - 1]} {prev_month_date.year}"


def is_recipient_format(value: str) -> bool:
    value = str(value or "").strip()

    pattern_with_name = r"^.+<[^<>\s@]+@[^<>\s@]+\.[^<>\s@]+>$"
    pattern_email_only = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

    return bool(
        re.match(pattern_with_name, value)
        or re.match(pattern_email_only, value)
    )


def get_recipients_from_tab(tab_key: str) -> list[str]:
    email_cfg = GSHEET["TYPE_YOUR_EMAIL_CONFIG_KEY"]

    df = read_sheet(
        email_cfg["sheet_id"],
        email_cfg["tabs"][tab_key],
    )

    if df.empty:
        return []

    first_col = df.columns[0]

    values = (
        df[first_col]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    recipients = [x for x in values if is_recipient_format(x)]

    seen = set()
    unique_recipients = []

    for recipient in recipients:
        if recipient not in seen:
            seen.add(recipient)
            unique_recipients.append(recipient)

    return unique_recipients


def get_lm_shared_recipients() -> tuple[list[str], list[str]]:
    cc_recipients = get_recipients_from_tab("TYPE_YOUR_CC_TAB_KEY")
    bcc_recipients = get_recipients_from_tab("TYPE_YOUR_BCC_TAB_KEY")

    return cc_recipients, bcc_recipients


def get_email_sender_from_config() -> tuple[str, str]:
    config_sheet = GSHEET["TYPE_YOUR_CONFIG_SHEET_KEY"]

    email_sender = get_cell_value(
        sheet_id=config_sheet["sheet_id"],
        tab_name=config_sheet["tabs"]["main"],
        cell="TYPE_YOUR_EMAIL_CELL",
    )

    app_password_sender = get_cell_value(
        sheet_id=config_sheet["sheet_id"],
        tab_name=config_sheet["tabs"]["main"],
        cell="TYPE_YOUR_PASSWORD_CELL",
    )

    if not email_sender:
        raise ValueError("Email sender is empty.")
    if not app_password_sender:
        raise ValueError("App password is empty.")

    return email_sender, app_password_sender


def build_link(url: str, text: str, color: str = "#1a73e8") -> str:
    return (
        f'<a href="{url}" target="_blank" '
        f'style="color:{color};text-decoration:underline;font-weight:600">'
        f"{text}</a>"
    )


def build_tracker_links_html(tracker_links: list[tuple[str, str]]) -> str:
    rows = []

    for label, tracker_key in tracker_links:
        tracker_url = GSHEET[tracker_key]["url"]
        rows.append(build_link(tracker_url, label))

    return "<br>".join(rows)


def build_tracker_links_text(tracker_links: list[tuple[str, str]]) -> str:
    rows = []

    for label, tracker_key in tracker_links:
        tracker_url = GSHEET[tracker_key]["url"]
        rows.append(f"{label}: {tracker_url}")

    return "\n".join(rows)


def build_html_lm_email(
    period_label: str,
    tracker_links: list[tuple[str, str]],
    sosialisasi_url: str,
) -> str:
    red_color = "#c62828"

    tracker_html = build_tracker_links_html(tracker_links)

    sosialisasi = build_link(sosialisasi_url, "LINK SOSIALISASI")
    sanggahan_xcld = build_link(
        SANGGAHAN_XCLD_URL,
        "Sanggahan XCLD",
        red_color,
    )
    sanggahan_non_xcld = build_link(
        SANGGAHAN_NON_XCLD_URL,
        "Sanggahan Non XCLD",
        red_color,
    )
    sanggahan_cluster = build_link(
        SANGGAHAN_CLUSTER_URL,
        "Sanggahan",
        red_color,
    )

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 13.5px; color: #222; line-height: 1.55;">
      <p>Dear all,</p>

      <p>Berikut adalah LINK untuk KPI performa bulan <b>{{period_label}}</b>.</p>

      <p>
        {{tracker_html}}
      </p>

      <p>
        Perhitungan KPI menggunakan skema penyesuaian KPI terbaru menyesuaikan sosialisasi pada link berikut:
        {{sosialisasi}}
      </p>

      <p><b>Sanggahan</b></p>

      <p>
        Khusus untuk sanggahan XCLD, mohon diinput TRID di {{sanggahan_xcld}}<br>
        Untuk sanggahan selain XCLD, dapat diinput di link berikut:<br>
        Station Level : {{sanggahan_non_xcld}}<br>
        Cluster Level : {{sanggahan_cluster}}
      </p>

      <p>
        Sanggahan harus diisi max tanggal <b>12 setiap bulannya</b>, lewat dari waktu yang ditentukan,
        gsheet akan terkunci dan sanggahan tidak diterima.
      </p>

      <p style="color:{{red_color}};">
        <b>*Mohon kerjasamanya untuk memastikan setiap sanggahan ditulis pada gsheet karena sanggahan yang tidak diinput tidak akan dihitung dalam KPI.</b>
      </p>

      <p>
        Kepada teman-teman RM, AM, Ops Spec, CH, Station feel free untuk meneruskan ke tim pickup terkait
        apabila ada yang terlewat dan menginformasikan apabila terdapat hub baru yang belum dimasukkan ke dalam tracker ini.
      </p>

      <br>

      <p>Terima kasih.</p>

      <p>Regards,<br><b>BI-Reporting</b></p>
    </body>
    </html>
    """.replace("{{period_label}}", period_label).replace("{{tracker_html}}", tracker_html).replace("{{sosialisasi}}", sosialisasi).replace("{{sanggahan_xcld}}", sanggahan_xcld).replace("{{sanggahan_non_xcld}}", sanggahan_non_xcld).replace("{{sanggahan_cluster}}", sanggahan_cluster).replace("{{red_color}}", red_color)


def build_plain_text(
    period_label: str,
    tracker_links: list[tuple[str, str]],
    sosialisasi_url: str,
) -> str:
    tracker_text = build_tracker_links_text(tracker_links)

    return (
        f"Dear all,\n\n"
        f"Berikut adalah LINK untuk KPI performa bulan {period_label}.\n\n"
        f"{tracker_text}\n\n"
        f"Perhitungan KPI menggunakan skema penyesuaian KPI terbaru menyesuaikan sosialisasi pada link berikut: {sosialisasi_url}\n\n"
        f"Sanggahan\n"
        f"Khusus untuk sanggahan XCLD, mohon diinput TRID di Sanggahan XCLD: {SANGGAHAN_XCLD_URL}\n"
        f"Untuk sanggahan selain XCLD, dapat diinput di link berikut:\n"
        f"Station Level: {SANGGAHAN_NON_XCLD_URL}\n"
        f"Cluster Level: {SANGGAHAN_CLUSTER_URL}\n\n"
        f"Sanggahan harus diisi max tanggal 12 setiap bulannya, lewat dari waktu yang ditentukan, gsheet akan terkunci dan sanggahan tidak diterima.\n\n"
        f"*Mohon kerjasamanya untuk memastikan setiap sanggahan ditulis pada gsheet karena sanggahan yang tidak diinput tidak akan dihitung dalam KPI.\n\n"
        f"Kepada teman-teman RM, AM, Ops Spec, CH, Station feel free untuk meneruskan ke tim pickup terkait apabila ada yang terlewat dan menginformasikan apabila terdapat hub baru yang belum dimasukkan ke dalam tracker ini.\n\n"
        f"Terima kasih.\n\n"
        f"Regards,\n"
        f"BI-Reporting"
    )


def send_email_chunked(
    smtp_user: str,
    smtp_password: str,
    to_recipients: list[str],
    cc_recipients: list[str],
    bcc_recipients: list[str],
    subject: str,
    html_body: str,
    plain_body: str,
    chunk_size: int = 50,
) -> None:
    if not to_recipients:
        raise ValueError("To recipients empty.")

    context = ssl.create_default_context()

    for i in range(0, len(to_recipients), chunk_size):
        to_chunk = to_recipients[i:i + chunk_size]

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SENDER_DISPLAY_NAME} <{SENDER_ALIAS_EMAIL}>"
        msg["To"] = ", ".join(to_chunk)

        if cc_recipients:
            msg["Cc"] = ", ".join(cc_recipients)

        all_recipients = to_chunk + cc_recipients + bcc_recipients

        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, all_recipients, msg.as_string())

        print(
            f"Sent chunk {i // chunk_size + 1}: "
            f"To={len(to_chunk)}, CC={len(cc_recipients)}, BCC={len(bcc_recipients)}"
        )


def run():
    print("=== DAY 2 LM EMAIL START ===")

    smtp_user, smtp_password = get_email_sender_from_config()

    cc_recipients, bcc_recipients = get_lm_shared_recipients()

    period_label = get_previous_month_label()

    for job in EMAIL_JOBS:
        area_label = job["area_label"]
        to_tab_key = job["to_tab_key"]
        tracker_links = job["tracker_links"]
        sosialisasi_url = job["sosialisasi_url"]

        to_recipients = get_recipients_from_tab(to_tab_key)

        if not to_recipients:
            print(f"[SKIP] {area_label}: To recipients empty")
            continue

        subject = f"(ID) LM KPI Progressive Tiering {area_label} - {period_label}"

        html_body = build_html_lm_email(
            period_label=period_label,
            tracker_links=tracker_links,
            sosialisasi_url=sosialisasi_url,
        )

        plain_body = build_plain_text(
            period_label=period_label,
            tracker_links=tracker_links,
            sosialisasi_url=sosialisasi_url,
        )

        print(f"\nSending {area_label}")
        print(f"To count: {len(to_recipients)}")
        print(f"CC count: {len(cc_recipients)}")
        print(f"BCC count: {len(bcc_recipients)}")
        print(f"Subject: {subject}")

        send_email_chunked(
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            subject=subject,
            html_body=html_body,
            plain_body=plain_body,
            chunk_size=50,
        )

    print("=== DAY 2 LM EMAIL DONE ===")


if __name__ == "__main__":
    run()
