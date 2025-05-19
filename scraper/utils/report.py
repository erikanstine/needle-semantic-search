import json
from contextlib import contextmanager
from time import perf_counter

from datetime import datetime
from pathlib import Path


class PipelineProfiler:
    """Record durations for pipeline steps."""

    def __init__(self):
        self.report = {
            "steps": {},
            "started_at": datetime.utcnow().isoformat(),
        }

    @contextmanager
    def record(self, step: str):
        start = perf_counter()
        yield
        self.report["steps"][step] = perf_counter() - start

    def finish(self) -> dict:
        self.report["ended_at"] = datetime.utcnow().isoformat()
        self.report["total_runtime_seconds"] = sum(self.report["steps"].values())
        return self.report


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


def print_pipeline_report(report: dict):
    print("\n⏳ Pipeline Timing Report")
    for step, dur in report.get("steps", {}).items():
        print(f"  {step}: {dur:.2f}s")
    print(f"  Total: {report.get('total_runtime_seconds', 0.0):.2f}s")


def save_pipeline_report(report: dict, path_prefix: str = "data/logs/"):
    dt = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    Path(path_prefix).mkdir(parents=True, exist_ok=True)
    path = Path(path_prefix) / f"pipeline_report_{dt}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"📝 Saved pipeline report to {path}")


def save_problematic_urls(urls):
    if urls:
        Path("data/skipped/").mkdir(parents=True, exist_ok=True)
        with open("data/skipped/problematic_urls.json", "w", encoding="utf-8") as f:
            json.dump(urls, f, indent=2)

        print(
            f"📝 Saved {len(urls)} problematic URLs to data/skipped/problematic_urls.json"
        )
