import json

from datetime import datetime
from pathlib import Path


def print_run_report(report):
    print("\n📊 Ingestion Report")
    print(f"  Total URLs: {report['total_urls']}")
    print(f"  ✅ Fetched: {len(report['fetched'])}")
    print(f"  ⏭️  Skipped: {len(report['skipped'])}")
    print(f"  ❌ Failed : {len(report['failed'])}")
    print(f"  ⏱️  Duration: {report['runtime_seconds']:.2f}s")

    if report["failed"]:
        print("\n❌ Failures:")
        for url, err in report["failed"].items():
            print(f"  - {url}: {err}")


def save_run_report(report, path_prefix="data/logs/"):
    dt = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = f"{path_prefix}run_report_{dt}.json"
    Path(path_prefix).mkdir(exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📝 Report saved to {path}")


def save_skipped_slugs(
    slugs: set, reason: str = "unknown", output_dir: str = "data/skipped/"
):
    if not slugs:
        return  # Nothing to save

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{reason}_skipped_slugs_{timestamp}.txt"
    path = Path(output_dir) / filename

    with open(path, "w", encoding="utf-8") as f:
        for slug in sorted(slugs):
            f.write(slug + "\n")

    print(f"📝 Saved {len(slugs)} skipped slugs to {path}")


def save_ingest_report(report: dict, mode: str = "ingest"):
    Path("data/logs/").mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{mode}_report_{timestamp}.json"
    path = Path("data/logs") / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"📝 Saved ingestion report to {path}")
