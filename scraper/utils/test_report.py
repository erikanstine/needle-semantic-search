import json
from scraper.utils.report import (
    save_skipped_slugs,
    save_problematic_urls,
    PipelineProfiler,
    save_pipeline_report,
)


def test_save_skipped_slugs(tmp_path):
    slugs = {"a", "b"}
    save_skipped_slugs(slugs, reason="test", output_dir=str(tmp_path))
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    content = set(files[0].read_text().splitlines())
    assert content == slugs


def test_save_problematic_urls(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_problematic_urls({"u": "err"})
    path = tmp_path / "data" / "skipped" / "problematic_urls.json"
    data = json.loads(path.read_text())
    assert data == {"u": "err"}


def test_pipeline_profiler_and_save(tmp_path):
    profiler = PipelineProfiler()
    with profiler.record("test"):
        pass
    report = profiler.finish()
    assert "test" in report["steps"]
    assert report["total_runtime_seconds"] >= 0
    save_pipeline_report(report, path_prefix=str(tmp_path) + "/")
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    saved = json.loads(files[0].read_text())
    assert saved["steps"] == report["steps"]
