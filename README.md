# qr-asset-tracker

A small inventory app for tracking physical assets with QR codes. It runs on a
laptop, stores everything in one CSV file, and is meant to be opened from a
phone on the same network: photograph an item's QR code, confirm where it is,
and the record is updated.

Built with Flask. QR codes are read on the server with OpenCV, so the phone only
needs a browser and a camera.

## What it does

- **Scan.** Upload a photo of a QR code, or type the asset ID. The app finds the
  record and opens an update form for location, status, maintenance state, and
  notes. Saving also stamps the scan time and adds one to the scan count.
- **Create.** Add a new asset to the inventory.
- **Browse.** Search every asset and open one to see its details and QR code.

While scanning, the app warns about things worth a second look:

- the item was already scanned in this session
- the asset ID is not in the inventory
- the item is somewhere other than its expected location

Text is tidied as it is saved, so the data stays consistent no matter how it was
typed. `classroom   mgmt` is stored as `Classroom Mgmt`, asset IDs are stored
uppercase without spaces, and empty values become `N/A`. Search ignores case and
spacing, so `room101` finds `Room 101`.

## Running it

You need Python 3.10 or newer.

```
git clone https://github.com/omarrsherif/qr-asset-tracker.git
cd qr-asset-tracker
```

Create a virtual environment and install the dependencies.

macOS and Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

In Command Prompt the activation command is `.venv\Scripts\activate.bat`. If
`py` is not available, use `python`.

Then, with the environment active, on any platform:

```
python generate_qrcodes.py
python app.py
```

`generate_qrcodes.py` writes one QR image per asset into `qrcodes/`, named like
`A001_qr.png`. Run it again after adding assets.

Open http://127.0.0.1:5000 on the laptop.

### Opening it on a phone

1. Connect the phone to the same Wi-Fi as the laptop.
2. Find the laptop's local IP address. The app prints the addresses it is
   listening on when it starts. You can also run `ipconfig getifaddr en0` on
   macOS, or `ipconfig` on Windows and read the IPv4 address of the active
   adapter.
3. Open that address with port 5000 on the phone, for example
   `http://192.168.1.25:5000`.

### Before you run it on a shared network

The app has no login, and it listens on every network interface so that a phone
can reach it. Anyone on the same network can view and change the inventory. Run
it on a network you trust.

Debug mode is off by default. Set `FLASK_DEBUG=1` to turn it on while
developing, and only on a network where you are the only user, because Flask's
debugger allows running code on the machine.

### Troubleshooting

- **PowerShell blocks the activation script.** Run
  `Set-ExecutionPolicy -Scope Process Bypass` in that window, then activate
  again.
- **Packages install into the wrong Python.** Use `python3 -m pip` on macOS and
  Linux, or `py -m pip` on Windows.
- **Port 5000 is already in use.** Stop the other program that is using it. On
  macOS this is often AirPlay Receiver, which can be turned off in System
  Settings.

## The data

Everything lives in `assets_demo.csv`, which ships with 455 made-up assets for a
school building. The app writes to this file directly, so using the app changes
it. `git restore assets_demo.csv` puts the demo data back.

| Column | Meaning |
| --- | --- |
| `asset_id` | Unique ID, also the text inside the QR code |
| `item_name`, `category`, `owner` | What the item is and who is responsible for it |
| `expected_location` | Where the item belongs |
| `current_location` | Where it was last scanned |
| `status` | `Active`, `Spare`, `In Repair`, or `Retired` |
| `maintenance_state` | `Good`, `Maintenance Due`, `Needs Battery`, `Needs Replacement`, `Restock Needed`, or `N/A` |
| `last_scanned`, `last_scan_location`, `scan_count` | Filled in by the scan flow |
| `notes` | Free text |

## Project layout

```
app.py                Flask app: routes, CSV loading and saving, normalization, QR decoding
generate_qrcodes.py   creates qrcodes/<asset_id>_qr.png for every asset
asset_inventory.py    the original terminal version of the scan flow
assets_demo.csv       the inventory
templates/            Jinja pages
static/style.css      styling on top of Bootstrap
qrcodes/              generated QR images (not committed)
```

`asset_inventory.py` is the console prototype the web app grew out of. It reads
and writes the same CSV and runs with `python asset_inventory.py`.

## Limits

- QR codes only. Barcodes are not read.
- Scanning works from an uploaded photo, not a live camera view.
- One CSV file with no locking, so it suits one person scanning at a time.
