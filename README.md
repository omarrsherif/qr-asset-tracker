# Local Inventory App

A lightweight inventory tracking app built with Flask and CSV storage.
It is designed to run locally on a laptop, with a simple browser-based interface that can also be opened from another device on the same network.

The project includes:

- A web app for scanning, creating, browsing, and reviewing inventory items
- CSV-backed storage for easy local use and portability
- QR code lookup from uploaded images
- A console demo script for simple terminal-based testing

## Features

- Home page with `Scan`, `Create`, and `Browse` flows
- Browse page with flexible asset search
- Asset detail page for reviewing a single record
- Scan flow with:
  - QR image upload lookup
  - manual asset ID lookup
  - duplicate scan warnings within the same session
  - unknown asset warnings
  - location mismatch warnings
  - scan count updates
  - status updates
  - maintenance state updates
  - notes updates
- Create flow for adding new inventory items to the CSV file
- Dropdown-based `Status` and `Maintenance state` fields in the web UI
- Case-insensitive and space-insensitive search
- Automatic normalization of legacy `NA` values to `N/A`
- QR code generation for every `asset_id`

## Project Structure

```text
app.py
assets_demo.csv
asset_inventory.py
generate_qrcodes.py
requirements.txt
README.md
templates/
static/
qrcodes/
```

## Requirements

Before running the project, make sure you have:

- Python 3.10 or newer recommended
- `pip` available in your Python installation

## Download Or Clone

You can get the project in either of these ways:

### Option 1: Clone with Git

```bash
git clone https://github.com/omarrsherif/Inventory-Project.git
cd Inventory-Project
```

### Option 2: Download as ZIP

1. Download the repository ZIP from GitHub.
2. Extract it anywhere on your computer.
3. Open a terminal in the extracted `Inventory-Project` folder.

The project does not need to live in a specific directory. You can run it from any location as long as you open the terminal in the project folder first.

## Setup

Create a virtual environment, activate it, and install the dependencies.

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

### Windows Command Prompt

```bat
py -m venv .venv
.venv\Scripts\activate.bat
py -m pip install -r requirements.txt
```

If `py` is not available on Windows, replace it with `python`.

## Run The Web App

### macOS and Linux

```bash
python3 app.py
```

### Windows PowerShell or Command Prompt

```powershell
py app.py
```

When the server starts, open:

```text
http://127.0.0.1:5000
```

The Flask app is configured to run on port `5000`.

## Open It On Another Device

The app listens on `0.0.0.0`, which means it can be opened from another device on the same local network.

1. Make sure your laptop and phone are connected to the same Wi-Fi network.
2. Find your computer's local IP address.
3. Open `http://YOUR_IP_ADDRESS:5000` on the other device.

Example:

```text
http://192.168.1.25:5000
```

Find your local IP address with:

### macOS

```bash
ipconfig getifaddr en0
```

If you are using Ethernet or `en0` does not return an address:

```bash
ifconfig
```

### Windows

```powershell
ipconfig
```

Look for the IPv4 address on your active network adapter.

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
- review item details

Browse search checks:

- `asset_id`
- `item_name`
- `category`
- `owner`
- `status`
- `expected_location`
- `current_location`

## Text Normalization Rules

The app normalizes several fields so data stays consistent even when users type values differently.

Current behavior:

- extra spaces are collapsed to a single space
- search ignores case differences
- search ignores spacing differences
- stored values are displayed in a normalized title-style format
- `asset_id` is stored uppercase with spaces removed
- blank placeholder-style values are stored as `N/A`

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

## Generate QR Codes

Run the QR code generator from the project folder.

### macOS and Linux

```bash
python3 generate_qrcodes.py
```

### Windows

```powershell
py generate_qrcodes.py
```

The script creates PNG files in the `qrcodes/` folder with names like:

```text
A001_qr.png
```

## Console Demo

The original terminal version is still included in:

```text
asset_inventory.py
```

This script is useful if you want a simpler console-based example alongside the Flask app.

## Data File

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

## QR Scanning Notes

- The current web app supports QR lookup from uploaded images
- Manual asset ID entry is still available
- The current project does not yet implement barcode reading in the main app flow

## Troubleshooting

- If the virtual environment activation command is blocked in PowerShell, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

- If `pip` installs to the wrong Python version, use `python3 -m pip` on macOS/Linux or `py -m pip` on Windows.
- If port `5000` is already in use, stop the other process using that port before starting the app again.

## License

Add a license section here if you plan to distribute or reuse the project publicly.
