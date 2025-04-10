import json

from datetime import datetime
from pathlib import Path


def print_run_report(report):
    print("\n📊 Ingestion Report")
    print(f"  Total URLs: {report['total_urls']}")
    print(f"  ✅ Scraped: {len(report['scraped'])}")
    print(f"  ⏭️  Skipped: {len(report['skipped'])}")
    print(f"  ❌ Failed : {len(report['failed'])}")
    print(f"  ⏱️  Duration: {report['runtime_seconds']:.2f}s")

    if report["failed"]:
        print("\n❌ Failures:")
        for url, err in report["failed"].items():
            print(f"  - {url}: {err}")


def save_run_report(report, path_prefix="logs/"):
    dt = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = f"{path_prefix}run_report_{dt}.json"
    Path(path_prefix).mkdir(exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📝 Report saved to {path}")
