import csv
from datetime import datetime
from pathlib import Path

CSV_FILE = Path(__file__).with_name("assets_demo.csv")
NOT_SCANNED_VALUE = "NA"
STATUS_OPTIONS = ["Active", "Spare", "In Repair", "Retired"]
MAINTENANCE_OPTIONS = [
    "Good",
    "Maintenance Due",
    "Needs Battery",
    "Needs Replacement",
    "Restock Needed",
]
NORMALIZED_FIELDS = ["category", "owner", "expected_location", "current_location"]


def simplify_text(value):
    return "".join(value.split()).casefold()


def collapse_spaces(value):
    return " ".join(value.strip().split())


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


def canonicalize_free_text(value):
    cleaned = collapse_spaces(value)
    if not cleaned:
        return ""
    return format_title_text(cleaned)


def build_field_indexes(assets):
    indexes = {field: {} for field in NORMALIZED_FIELDS}

    for asset in assets.values():
        for field in NORMALIZED_FIELDS:
            value = collapse_spaces(asset[field])
            if value:
                indexes[field][simplify_text(value)] = value

    return indexes


def normalize_with_index(value, field_name, field_indexes):
    cleaned = collapse_spaces(value)
    if not cleaned:
        return ""

    key = simplify_text(cleaned)
    known_value = field_indexes[field_name].get(key)
    if known_value:
        return known_value

    normalized = canonicalize_free_text(cleaned)
    field_indexes[field_name][simplify_text(normalized)] = normalized
    return normalized


def normalize_asset_record(asset, field_indexes):
    for field in NORMALIZED_FIELDS:
        asset[field] = normalize_with_index(asset[field], field, field_indexes)

    asset["status"] = canonicalize_option(asset["status"], STATUS_OPTIONS)
    asset["maintenance_state"] = canonicalize_option(asset["maintenance_state"], MAINTENANCE_OPTIONS)


def canonicalize_option(value, options):
    key = simplify_text(value)
    for option in options:
        if simplify_text(option) == key:
            return option
    raise ValueError(f"Unsupported option: {value}")


def prompt_for_text_field(label, current_value, field_name, field_indexes):
    prompt = f"{label} [{current_value}]: "
    new_value = input(prompt).strip()
    if not new_value:
        return current_value
    return normalize_with_index(new_value, field_name, field_indexes)


def prompt_for_option(label, options, current_value):
    print(f"\n{label}:")
    for index, option in enumerate(options, start=1):
        marker = " (current)" if option == current_value else ""
        print(f"  {index} = {option}{marker}")

    while True:
        choice = input(f"Choose {label.lower()} [Enter keeps {current_value}]: ").strip()
        if not choice:
            return current_value
        if choice.isdigit():
            option_index = int(choice) - 1
            if 0 <= option_index < len(options):
                return options[option_index]
        print(f"Invalid choice. Pick 1 to {len(options)}, or press Enter to keep the current value.")

def load_assets():
    assets = {}
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["last_scanned"].strip():
                row["last_scanned"] = NOT_SCANNED_VALUE
            if not row["last_scan_location"].strip():
                row["last_scan_location"] = NOT_SCANNED_VALUE
            assets[row["asset_id"]] = row
    field_indexes = build_field_indexes(assets)
    for asset in assets.values():
        normalize_asset_record(asset, field_indexes)
    return assets

def save_assets(assets):
    fieldnames = [
        "asset_id","item_name","category","expected_location","current_location",
        "status","owner","maintenance_state","last_scanned","last_scan_location","scan_count","notes"
    ]
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for asset_id in sorted(assets):
            asset = assets[asset_id].copy()
            asset.setdefault("notes", NOT_SCANNED_VALUE)
            writer.writerow(asset)

def print_asset(asset):
    print(f"  ID: {asset['asset_id']}")
    print(f"  Item: {asset['item_name']}")
    print(f"  Category: {asset['category']}")
    print(f"  Owner: {asset['owner']}")
    print(f"  Expected location: {asset['expected_location']}")
    print(f"  Current location:  {asset['current_location']}")
    print(f"  Status: {asset['status']}")
    print(f"  Maintenance state: {asset['maintenance_state']}")
    print(f"  Scan count: {asset['scan_count']}")
    print(f"  Last scanned: {asset['last_scanned']}")
    print(f"  Last scan location: {asset['last_scan_location']}")

def check_asset_id_exception(assets, scanned_id, seen_this_session):
    scanned_id = scanned_id.strip().upper()

    if scanned_id not in assets:
        print("\n[EXCEPTION] Unknown asset ID.")
        print("  Action: flag for review or create a new record.")
        return None

    if scanned_id in seen_this_session:
        print("\n[EXCEPTION] Duplicate scan in this audit session.")
        print("  Action: ignore or confirm whether this was intentional.")

    return scanned_id

def scan_asset(assets, scanned_id, scan_location, seen_this_session, field_indexes):
    scanned_id = scanned_id.strip().upper()
    scan_location = normalize_with_index(scan_location, "current_location", field_indexes)

    asset = assets[scanned_id]

    if scanned_id not in seen_this_session:
        seen_this_session.add(scanned_id)

    if simplify_text(scan_location) != simplify_text(asset["expected_location"]):
        print("\n[EXCEPTION] Location mismatch.")
        print(f"  Expected: {asset['expected_location']}")
        print(f"  Scanned in: {scan_location}")
        print("  Action: flag item as misplaced or update location after verification.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset["last_scanned"] = now
    asset["last_scan_location"] = scan_location
    asset["current_location"] = scan_location
    asset["scan_count"] = str(int(asset["scan_count"]) + 1)

    print("\n[OK] Asset record updated.")
    print_asset(asset)


def edit_asset_details(assets, field_indexes):
    asset_id = input("Enter asset ID to edit (example: A001): ").strip().upper()
    if asset_id not in assets:
        print("\n[EXCEPTION] Unknown asset ID.")
        print("  Action: enter a valid asset ID from the file.")
        return

    asset = assets[asset_id]
    print("\nEditing asset:")
    print_asset(asset)

    asset["category"] = prompt_for_text_field("Category", asset["category"], "category", field_indexes)
    asset["owner"] = prompt_for_text_field("Owner", asset["owner"], "owner", field_indexes)
    asset["expected_location"] = prompt_for_text_field(
        "Expected location", asset["expected_location"], "expected_location", field_indexes
    )
    asset["current_location"] = prompt_for_text_field(
        "Current location", asset["current_location"], "current_location", field_indexes
    )
    asset["status"] = prompt_for_option("Status", STATUS_OPTIONS, asset["status"])
    asset["maintenance_state"] = prompt_for_option(
        "Maintenance state", MAINTENANCE_OPTIONS, asset["maintenance_state"]
    )

    print("\n[OK] Asset details updated.")
    print_asset(asset)

def show_missing_assets(assets, seen_this_session):
    missing = [a for a in assets.values() if a["asset_id"] not in seen_this_session]
    print("\n=== Missing / Not Yet Scanned In This Session ===")
    if not missing:
        print("All assets in the file were scanned during this session.")
        return
    for asset in missing:
        print(f"- {asset['asset_id']} | {asset['item_name']} | expected in {asset['expected_location']}")

def list_assets(assets):
    print("\n=== Current Asset Table ===")
    for asset_id in sorted(assets):
        a = assets[asset_id]
        print(
            f"{a['asset_id']}: {a['item_name']} | expected={a['expected_location']} | "
            f"current={a['current_location']} | scans={a['scan_count']}"
        )

def print_commands():
    print("\nCommands:")
    print("  1 = scan an asset")
    print("  2 = list all assets")
    print("  3 = show assets not scanned yet")
    print("  4 = edit asset details")
    print("  5 = reset session scan list")
    print("  6 = quit")

def main():
    assets = load_assets()
    field_indexes = build_field_indexes(assets)
    seen_this_session = set()

    print("Simple Asset Scan Demo")
    print("----------------------")
    print("This simulates how a barcode/QR scan updates an inventory record.")
    print("In real life, many scanners just type the asset ID into the program.")

    while True:
        print_commands()
        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            scanned_id = input("Enter scanned asset ID (example: A001): ").strip()
            scanned_id = check_asset_id_exception(assets, scanned_id, seen_this_session)
            if not scanned_id:
                continue
            scan_location = input("Enter scan location (example: Room 101): ").strip()
            scan_asset(assets, scanned_id, scan_location, seen_this_session, field_indexes)
            save_assets(assets)

        elif choice == "2":
            list_assets(assets)

        elif choice == "3":
            show_missing_assets(assets, seen_this_session)

        elif choice == "4":
            edit_asset_details(assets, field_indexes)
            save_assets(assets)

        elif choice == "5":
            seen_this_session.clear()
            print("Session scan list cleared.")

        elif choice == "6":
            save_assets(assets)
            print("Goodbye.")
            break

        else:
            print("Invalid choice. Pick 1, 2, 3, 4, 5, or 6.")

if __name__ == "__main__":
    main()
