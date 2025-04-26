import json
import os
import argparse

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=False)
load_dotenv(dotenv_path=".env.local", override=True)

project_root = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser(description="Migrate old manifest to new format")
parser.add_argument(
    "--dry_run",
    action="store_true",
    help="Perform a dry run without writing output files",
)
args = parser.parse_args()

# Load your old manifest
with open(project_root / os.getenv("DEFAULT_STORE_PATH")) as f:
    old_data = json.load(f)

new_manifest = {}
errors = []

html_root = project_root / "data" / "html"


for url, info in old_data.items():
    company = info.get("company", "").lower()
    if not company:
        errors.append((url, None))
        continue

    quarter = info["quarter"].lower().replace(" ", "")  # Q3 2025 → q32025
    year = quarter[-4:]  # last 4 chars
    q = quarter[:-4]  # rest is the quarter

    slug = f"{company}-{q}-{year}"

    # Verify expected HTML file exists
    expected_html_path = html_root / company / f"{q}-{year}.html"

    if not expected_html_path.exists():
        errors.append((slug, expected_html_path))
        continue  # Skip adding this one to new manifest

    new_manifest[slug] = {
        "url": url,
        "discovered_at": info.get("discovered_at"),
        "html_saved": info.get("status") == "fetched",
        "parsed": False,
        "embedded": False,
        "failed_at_step": None,
        "last_attempt": info.get("fetched_at", None),
    }

if args.dry_run:
    print(f"✅ Would migrate {len(new_manifest)} entries into new manifest format.")
    if errors:
        print(f"⚠️ {len(errors)} entries missing expected HTML files!")
        for slug, path in errors:
            print(f"  Missing for {slug}: {path}")
else:
    # Write only successful entries
    output_dir = project_root / "data" / "status"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(new_manifest, f, indent=2)

    print(f"✅ Migrated {len(new_manifest)} entries into new manifest format.")

    if errors:
        print(f"⚠️ {len(errors)} entries missing expected HTML files!")
        for slug, path in errors:
            print(f"  Missing for {slug}: {path}")
