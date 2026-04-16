import csv
import secrets
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "assets_demo.csv"
NOT_AVAILABLE = "N/A"
FIELDNAMES = [
    "asset_id",
    "item_name",
    "category",
    "expected_location",
    "current_location",
    "status",
    "owner",
    "maintenance_state",
    "last_scanned",
    "last_scan_location",
    "scan_count",
    "notes",
]
STATUS_OPTIONS = ["Active", "Spare", "In Repair", "Retired"]
MAINTENANCE_OPTIONS = [
    "Good",
    "Maintenance Due",
    "Needs Battery",
    "Needs Replacement",
    "Restock Needed",
]
NORMALIZED_TEXT_FIELDS = [
    "item_name",
    "category",
    "expected_location",
    "current_location",
    "owner",
]


def normalize_value(value):
    text = (value or "").strip()
    if text.upper() == "NA":
        return NOT_AVAILABLE
    return text if text else NOT_AVAILABLE


def collapse_spaces(value):
    return " ".join((value or "").strip().split())


def simplify_text(value):
    return collapse_spaces(value).replace(" ", "").casefold()


def format_title_text(value):
    small_words = {"and", "or", "of", "the", "in", "on", "for", "to"}
    words = collapse_spaces(value).split()
    formatted_words = []

    for index, word in enumerate(words):
        if word.isupper() or any(char.isdigit() for char in word):
            formatted_words.append(word)
            continue

        lowered = word.lower()
        if index > 0 and lowered in small_words:
            formatted_words.append(lowered)
        else:
            formatted_words.append(lowered.capitalize())

    return " ".join(formatted_words)


def normalize_text_field(value):
    cleaned = collapse_spaces(value)
    if not cleaned or cleaned == NOT_AVAILABLE:
        return NOT_AVAILABLE
    return format_title_text(cleaned)


def normalize_asset_id(value):
    compact = collapse_spaces(value).replace(" ", "")
    return compact.upper() if compact else ""


def normalize_option(value, options, allow_blank=False, blank_value=NOT_AVAILABLE):
    cleaned = collapse_spaces(value)
    if not cleaned:
        return blank_value if allow_blank else ""

    if simplify_text(cleaned) == simplify_text(blank_value):
        return blank_value

    normalized_key = simplify_text(cleaned)
    for option in options:
        if simplify_text(option) == normalized_key:
            return option

    return None


def normalize_asset_record(asset):
    normalized = dict(asset)
    normalized["asset_id"] = normalize_asset_id(normalized.get("asset_id", ""))

    for field in NORMALIZED_TEXT_FIELDS:
        normalized[field] = normalize_text_field(normalized.get(field, ""))

    normalized["status"] = normalize_option(normalized.get("status", ""), STATUS_OPTIONS) or NOT_AVAILABLE
    normalized["maintenance_state"] = normalize_option(
        normalized.get("maintenance_state", ""),
        MAINTENANCE_OPTIONS,
        allow_blank=True,
        blank_value=NOT_AVAILABLE,
    )
    normalized["last_scanned"] = normalize_value(normalized.get("last_scanned", ""))
    normalized["last_scan_location"] = normalize_text_field(normalized.get("last_scan_location", ""))
    normalized["scan_count"] = collapse_spaces(normalized.get("scan_count", "")) or "0"
    normalized["notes"] = normalize_value(normalized.get("notes", ""))
    return normalized


def load_assets():
    assets = {}
    with open(CSV_FILE, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            asset = {}
            for field in FIELDNAMES:
                asset[field] = normalize_value(row.get(field, ""))
            asset = normalize_asset_record(asset)
            if asset["scan_count"] == NOT_AVAILABLE:
                asset["scan_count"] = "0"
            assets[asset["asset_id"]] = asset
    return assets


def save_assets(assets):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for asset_id in sorted(assets):
            writer.writerow(normalize_asset_record(assets[asset_id]))


def get_session_scans():
    scanned_ids = session.get("scanned_ids", [])
    return set(scanned_ids)


def save_session_scans(scanned_ids):
    session["scanned_ids"] = sorted(scanned_ids)


def reset_scan_flow():
    session.pop("current_scanned_asset_id", None)


def build_scan_context(asset, scanned_ids):
    warnings = []
    if asset["asset_id"] in scanned_ids:
        warnings.append("Duplicate scan in this session. The item was already scanned once.")
    if asset["last_scanned"] != NOT_AVAILABLE:
        warnings.append(f"Last scanned on {asset['last_scanned']} at {asset['last_scan_location']}.")
    return {"asset": asset, "warnings": warnings}


def validate_required(form, field_names):
    errors = []
    cleaned = {}

    for field_name in field_names:
        value = form.get(field_name, "").strip()
        cleaned[field_name] = value
        if not value:
            label = field_name.replace("_", " ").title()
            errors.append(f"{label} is required.")

    return cleaned, errors


def render_with_options(template_name, **context):
    return render_template(
        template_name,
        status_options=STATUS_OPTIONS,
        maintenance_options=MAINTENANCE_OPTIONS,
        **context,
    )


def decode_qr_from_upload(uploaded_file):
    file_bytes = uploaded_file.read()
    uploaded_file.stream.seek(0)

    if not file_bytes:
        return None

    image_array = np.frombuffer(file_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        return None

    detector = cv2.QRCodeDetector()
    qr_value, _, _ = detector.detectAndDecode(image)
    qr_value = (qr_value or "").strip().upper()
    return qr_value or None


def filter_assets(asset_query):
    assets = load_assets()
    query = collapse_spaces(asset_query)
    normalized_query = simplify_text(query)
    asset_list = sorted(assets.values(), key=lambda asset: asset["asset_id"])

    if not normalized_query:
        return asset_list, query

    filtered_assets = []
    for asset in asset_list:
        searchable_text = simplify_text(
            " ".join(
            [
                asset["asset_id"],
                asset["item_name"],
                asset["category"],
                asset["owner"],
                asset["status"],
                asset["expected_location"],
                asset["current_location"],
            ]
            )
        )
        if normalized_query in searchable_text:
            filtered_assets.append(asset)

    return filtered_assets, query


@app.route("/")
def home():
    return render_with_options("home.html")


@app.route("/assets")
def assets_page():
    filtered_assets, query = filter_assets(request.args.get("q", ""))
    return render_with_options("assets.html", assets=filtered_assets, query=query)


@app.route("/assets/<asset_id>")
def asset_detail(asset_id):
    assets = load_assets()
    asset_id = asset_id.strip().upper()

    if asset_id not in assets:
        flash(f"Unknown asset ID: {asset_id}", "error")
        return redirect(url_for("assets_page"))

    return render_with_options("asset_detail.html", asset=assets[asset_id])


@app.route("/scan")
def scan_page():
    return render_with_options("scan.html")


@app.post("/scan/lookup")
def scan_lookup():
    asset_id = request.form.get("asset_id", "").strip().upper()

    if not asset_id:
        flash("Scan a QR code or enter an asset ID first.", "error")
        return redirect(url_for("scan_page"))

    assets = load_assets()
    if asset_id not in assets:
        flash(f"Unknown asset ID: {asset_id}", "error")
        return redirect(url_for("scan_page"))

    session["current_scanned_asset_id"] = asset_id
    return redirect(url_for("scan_details", asset_id=asset_id))


@app.post("/scan/photo")
def scan_photo_lookup():
    uploaded_file = request.files.get("qr_image")

    if not uploaded_file or not uploaded_file.filename:
        flash("Choose a photo first.", "error")
        return redirect(url_for("scan_page"))

    asset_id = decode_qr_from_upload(uploaded_file)
    if not asset_id:
        flash("No QR code was found in that image. Try a clearer photo or enter the asset ID manually.", "error")
        return redirect(url_for("scan_page"))

    assets = load_assets()
    if asset_id not in assets:
        flash(f"Unknown asset ID: {asset_id}", "error")
        return redirect(url_for("scan_page"))

    session["current_scanned_asset_id"] = asset_id
    return redirect(url_for("scan_details", asset_id=asset_id))


@app.route("/scan/<asset_id>")
def scan_details(asset_id):
    assets = load_assets()
    asset_id = asset_id.strip().upper()

    if asset_id not in assets:
        flash(f"Unknown asset ID: {asset_id}", "error")
        return redirect(url_for("scan_page"))

    session["current_scanned_asset_id"] = asset_id
    scanned_ids = get_session_scans()
    context = build_scan_context(assets[asset_id], scanned_ids)
    return render_with_options("scan_form.html", **context, form_values={})


@app.post("/scan/<asset_id>/submit")
def submit_scan(asset_id):
    assets = load_assets()
    asset_id = asset_id.strip().upper()

    if asset_id not in assets:
        flash(f"Unknown asset ID: {asset_id}", "error")
        return redirect(url_for("scan_page"))

    asset = assets[asset_id]
    form_values, errors = validate_required(
        request.form,
        ["scan_location", "status", "notes"],
    )

    form_values["scan_location"] = normalize_text_field(form_values["scan_location"])
    selected_status = normalize_option(form_values["status"], STATUS_OPTIONS)
    selected_maintenance_state = normalize_option(
        request.form.get("maintenance_state", ""),
        MAINTENANCE_OPTIONS,
        allow_blank=True,
        blank_value=NOT_AVAILABLE,
    )
    if selected_status is None:
        errors.append("Status must be selected from the dropdown.")
    else:
        form_values["status"] = selected_status

    if selected_maintenance_state is None:
        errors.append("Maintenance State must be selected from the dropdown.")
        form_values["maintenance_state"] = collapse_spaces(request.form.get("maintenance_state", ""))
    else:
        form_values["maintenance_state"] = selected_maintenance_state

    scanned_ids = get_session_scans()
    warnings = build_scan_context(asset, scanned_ids)["warnings"]

    if errors:
        return render_with_options(
            "scan_form.html",
            asset=asset,
            warnings=warnings,
            errors=errors,
            form_values=form_values,
        )

    scan_location = form_values["scan_location"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if simplify_text(scan_location) != simplify_text(asset["expected_location"]):
        warnings.append(
            f"Location mismatch. Expected {asset['expected_location']} but scanned in {scan_location}."
        )

    asset["current_location"] = scan_location
    asset["last_scan_location"] = scan_location
    asset["last_scanned"] = now
    asset["scan_count"] = str(int(asset["scan_count"]) + 1)
    asset["status"] = form_values["status"]
    asset["notes"] = form_values["notes"]
    asset["maintenance_state"] = form_values["maintenance_state"]

    scanned_ids.add(asset_id)
    save_session_scans(scanned_ids)
    save_assets(assets)

    return render_with_options(
        "scan_success.html",
        asset=asset,
        warnings=warnings,
    )


@app.route("/scan/back")
def back_from_scan():
    reset_scan_flow()
    return redirect(url_for("home"))


@app.route("/scan/reset")
def reset_scan_page():
    reset_scan_flow()
    return redirect(url_for("scan_page"))


@app.route("/add-item", methods=["GET", "POST"])
def add_item():
    form_values = {
        "asset_id": "",
        "item_name": "",
        "category": "",
        "expected_location": "",
        "current_location": "",
        "status": "",
        "owner": "",
        "maintenance_state": NOT_AVAILABLE,
        "notes": "",
    }
    errors = []

    if request.method == "POST":
        for key in form_values:
            form_values[key] = collapse_spaces(request.form.get(key, ""))

        required_fields = [
            "asset_id",
            "item_name",
            "category",
            "expected_location",
            "current_location",
            "status",
            "owner",
            "notes",
        ]

        for field_name in required_fields:
            if not form_values[field_name]:
                label = field_name.replace("_", " ").title()
                errors.append(f"{label} is required.")

        form_values["asset_id"] = normalize_asset_id(form_values["asset_id"])
        for field_name in NORMALIZED_TEXT_FIELDS:
            form_values[field_name] = normalize_text_field(form_values[field_name])

        selected_status = normalize_option(form_values["status"], STATUS_OPTIONS)
        if selected_status is None:
            errors.append("Status must be selected from the dropdown.")
        else:
            form_values["status"] = selected_status

        selected_maintenance_state = normalize_option(
            form_values["maintenance_state"],
            MAINTENANCE_OPTIONS,
            allow_blank=True,
            blank_value=NOT_AVAILABLE,
        )
        if selected_maintenance_state is None:
            errors.append("Maintenance State must be selected from the dropdown.")
        else:
            form_values["maintenance_state"] = selected_maintenance_state

        assets = load_assets()
        if form_values["asset_id"] and form_values["asset_id"] in assets:
            errors.append(f"Asset ID {form_values['asset_id']} already exists.")

        if not errors:
            new_asset = {
                "asset_id": form_values["asset_id"],
                "item_name": form_values["item_name"],
                "category": form_values["category"],
                "expected_location": form_values["expected_location"],
                "current_location": form_values["current_location"],
                "status": form_values["status"],
                "owner": form_values["owner"],
                "maintenance_state": form_values["maintenance_state"],
                "last_scanned": NOT_AVAILABLE,
                "last_scan_location": NOT_AVAILABLE,
                "scan_count": "0",
                "notes": form_values["notes"],
            }
            assets[new_asset["asset_id"]] = new_asset
            save_assets(assets)

            return render_with_options("add_success.html", asset=new_asset)

    return render_with_options("add_item.html", form_values=form_values, errors=errors)


@app.route("/add-item/back")
def back_from_add_item():
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
