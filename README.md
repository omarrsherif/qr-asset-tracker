# Local Inventory App

This project is a local inventory web app built with Flask and CSV storage.
It is designed to be simple to run on a laptop and easy to use from a phone or another device on the same network.

The app includes three main flows:

- `Scan`
- `Create`
- `Browse`

It also keeps the original console demo in `asset_inventory_demo.py` for comparison and simple terminal-based testing.

## Current Features

- Home page with matching `Scan`, `Create`, and `Browse` action cards
- Browse page for searching and opening asset records
- Asset detail page for reviewing a single item
- Scan flow with:
  - QR image upload lookup
  - manual asset ID lookup
  - duplicate scan warnings in the same session
  - unknown asset warnings
  - location mismatch warnings
  - scan count updates
  - status updates
  - maintenance state updates
  - notes updates
- Create flow for adding new inventory items to the CSV
- `Status` and `Maintenance state` as dropdown fields in the web UI
- Shared text normalization for:
  - `item_name`
  - `category`
  - `owner`
  - `expected_location`
  - `current_location`
  - scan location input
- Case-insensitive and space-insensitive search in Browse
- Automatic normalization of legacy `NA` values to `N/A`
- QR code generation script for every `asset_id`
- Bottom-right site credit

## Text Normalization Rules

The app normalizes several text fields so records stay consistent even if users type values differently.

Current behavior:

- Extra spaces are collapsed to a single space
- Search ignores case differences
- Search ignores spacing differences
- Stored values are displayed in a normalized title-style format
- `asset_id` is stored uppercase with spaces removed
- Blank placeholder-style values are stored as `N/A`

Examples:

- `classroom   mgmt` becomes `Classroom Mgmt`
- `room101` and `Room 101` are treated consistently in search
- `na` is normalized to `N/A`

## Dropdown Options

### Status

- `Active`
- `Spare`
- `In Repair`
- `Retired`

### Maintenance State

- `N/A`
- `Good`
- `Maintenance Due`
- `Needs Battery`
- `Needs Replacement`
- `Restock Needed`

## Project Structure

```text
app.py
assets_demo.csv
asset_inventory_demo.py
generate_qrcodes.py
requirements.txt
README.md
templates/
static/
qrcodes/
```

## Main Files

- `app.py`
  Main Flask application, CSV loading/saving, normalization rules, search, scan flow, and create flow.

- `assets_demo.csv`
  Demo inventory data used by both the web app and the console demo.

- `asset_inventory_demo.py`
  Original console-based inventory demo script.

- `generate_qrcodes.py`
  Generates QR code images for asset IDs.

- `templates/`
  Jinja templates for the web UI.

- `static/style.css`
  Shared styling for the app UI.

## How To Run

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install the requirements:

```powershell
pip install -r requirements.txt
```

3. Start the Flask app:

```powershell
python app.py
```

4. Open the app locally:

```text
http://127.0.0.1:5000
```

5. To use it on your phone, open the laptop's local IP address on the same Wi-Fi network.

Example:

```text
http://192.168.1.25:5000
```

To find your laptop IP on Windows:

```powershell
ipconfig
```

Look for the IPv4 address on your active Wi-Fi adapter.

## Using The App

### Scan

Use the Scan flow to update an existing asset.

You can:

- upload a QR image
- enter an asset ID manually
- review warnings before saving
- update location, status, maintenance state, and notes

When a scan is submitted, the app updates:

- `current_location`
- `last_scan_location`
- `last_scanned`
- `scan_count`
- `status`
- `maintenance_state`
- `notes`

### Create

Use the Create flow to add a new item to inventory.

The form includes:

- asset ID
- item name
- category
- owner
- expected location
- current location
- status
- maintenance state
- notes

### Browse

Use the Browse flow to:

- search the asset list
- open a single asset record
- review item details before updating

Browse search checks:

- `asset_id`
- `item_name`
- `category`
- `owner`
- `status`
- `expected_location`
- `current_location`

## Generate QR Codes

Run:

```powershell
python generate_qrcodes.py
```

The script creates PNG files in the `qrcodes/` folder with names like:

```text
A001_qr.png
```

## CSV Fields

The app stores data in `assets_demo.csv` with these columns:

- `asset_id`
- `item_name`
- `category`
- `expected_location`
- `current_location`
- `status`
- `owner`
- `maintenance_state`
- `last_scanned`
- `last_scan_location`
- `scan_count`
- `notes`

## Placeholder Values

The app uses `N/A` as the standard placeholder for missing or unset values.

This applies to fields such as:

- `maintenance_state`
- `last_scanned`
- `last_scan_location`
- `notes`

Older `NA` values are normalized automatically when data is loaded and saved.

## Notes About QR Scanning

- The current web app supports QR lookup from uploaded images
- Manual asset ID entry is still available
- The current project does not yet implement barcode reading in the main app flow
- Barcode label generation was discussed separately, but QR lookup remains the active scanning path in this app

## Console Demo

The original terminal version still exists in:

```text
asset_inventory_demo.py
```

That script is useful if you want a simpler console-based example alongside the Flask version.
