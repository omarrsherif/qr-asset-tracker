import csv
from pathlib import Path

import qrcode

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "assets_demo.csv"
OUTPUT_DIR = BASE_DIR / "qrcodes"


def generate_qr_codes():
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(CSV_FILE, newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        count = 0

        for row in reader:
            asset_id = (row.get("asset_id") or "").strip().upper()
            if not asset_id:
                continue

            image = qrcode.make(asset_id)
            output_path = OUTPUT_DIR / f"{asset_id}_qr.png"
            image.save(output_path)
            count += 1

    print(f"Created {count} QR code image(s) in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_qr_codes()
