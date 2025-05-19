import argparse
import asyncio
import concurrent.futures
import json
import os
from contextlib import nullcontext

from tqdm import tqdm

from chunk_processor import ChunkProcessor
from crawler_manager import get_urls_and_store
from html_fetcher import HTMLFetcher
from parser import Parser
from status_tracker import StatusTracker

from utils.report import (
    print_run_report,
    save_run_report,
    save_skipped_slugs,
    save_ingest_report,
    PipelineProfiler,
    print_pipeline_report,
    save_pipeline_report,
)
from utils.storage import TranscriptKey


def run_ingest(st: StatusTracker, dry_run: bool, force: bool, profiler: PipelineProfiler | None = None):
    chunks = []
    if force:
        print(
            "⚠️  --force is True: All slugs will be reprocessed, even if already parsed."
        )
        slugs_to_parse = list(st.data.keys())[:1]
    else:
        print("ℹ️  --force is False: Only unparsed slugs will be processed.")
        slugs_to_parse = st.filter_for(step="parsed", status=False)

    parse_ctx = profiler.record("parse") if profiler else nullcontext()
    with parse_ctx:
        for slug in tqdm(slugs_to_parse, desc="Parsing transcripts"):
            tk = TranscriptKey.from_slug(slug)
            html_path = tk.to_path(data_root="data")

            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    parser = Parser.from_html(f.read(), tk, st.get_url(tk.slug()))
                    chunks.extend(parser.parse_html())
                if not dry_run:
                    st.mark_success(tk.slug(), "parsed")
                else:
                    print(f"🚫 Dry run: Would have marked {slug} as parsed.")
            except Exception as e:
                if not dry_run:
                    st.mark_failure(tk.slug(), "parsed", str(e))
                else:
                    print(f"🚫 Dry run: Would have marked {slug} as failed.\n{e}")

    processor = ChunkProcessor(chunks)
    if not dry_run:
        if profiler:
            with profiler.record("embed"):
                processor.embed()
            with profiler.record("upsert"):
                processor.upsert()
        else:
            processor.embed()
            processor.upsert()
        for slug in processor.get_successful_slugs():
            st.mark_success(slug, "embedded")
        for slug in processor.get_failed_slugs():
            st.mark_failure(slug, "embedded", "Embedding or upsert failed")
        st.save()
        save_skipped_slugs(processor.get_failed_slugs(), reason="embedding")
    else:
        print(f"🚫 Dry run: Would have embedded and upserted {len(chunks)} chunks.")
        for slug in processor.get_successful_slugs():
            print(f"🚫 Dry run: Would have marked {slug} as embedded success.")
        for slug in processor.get_failed_slugs():
            print(f"🚫 Dry run: Would have marked {slug} as embedded failure.")

    return processor.get_report()


def main():
    st = StatusTracker()
    parser = argparse.ArgumentParser(description="Transcript Ingestion Pipeline")
    parser.add_argument(
        "step",
        choices=[
            "crawl",
            "fetch",
            "ingest",
            "profile",
            "retry",
            "refresh_metadata",
            "extract_candidates",
            "regenerate_snippets",
        ],
        help="Step to run: 'crawl', 'fetch', 'ingest', 'profile' or 'retry'",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Run pipeline steps without any live requests",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scraping URLs even if already marked as scraped",
    )
    parser.add_argument(
        "--skipped_file",
        type=str,
        default=None,
        help="Path to a skipped slugs .txt file to retry",
    )
    args = parser.parse_args()

    if args.step == "crawl":
        urls = get_urls_and_store(force=args.force)
        if not urls:
            print("No new transcripts found.")
        else:
            print(f"Discovered {len(urls)} new transcript URLs.")

    elif args.step == "fetch":
        try:
            with open("data/urls_to_scrape.json") as f:
                url_list = json.load(f)
            fetcher = HTMLFetcher(st, url_list, force=args.force)
            fetcher.fetch()
            report = fetcher.get_report()
            print_run_report(report)
            save_run_report(report)
        except FileNotFoundError:
            print("No cached URL list found. Run 'crawl' first.")

    elif args.step == "ingest":
        report = run_ingest(st, args.dry_run, args.force)
        save_ingest_report(report, args.step)

    elif args.step == "profile":
        profiler = PipelineProfiler()
        with profiler.record("crawl"):
            urls = get_urls_and_store(force=args.force)
        with profiler.record("fetch"):
            if urls:
                fetcher = HTMLFetcher(st, urls, force=args.force)
                fetcher.fetch()
        ingest_report = run_ingest(st, args.dry_run, args.force, profiler)
        pipeline_report = profiler.finish()
        pipeline_report["ingest"] = ingest_report
        print_pipeline_report(pipeline_report)
        save_pipeline_report(pipeline_report)

    elif args.step == "retry":
        # Load slugs to retry
        if args.skipped_file is not None:
            # Load slugs from skipped slugs file
            try:
                with open(args.skipped_file, "r", encoding="utf-8") as f:
                    slugs_to_retry = [line.strip() for line in f if line.strip()]
                print(f"Loaded {len(slugs_to_retry)} slugs from skipped slugs file.")
            except FileNotFoundError:
                print(f"Skipped slugs file '{args.skipped_file}' not found.")
                return
        else:
            # Load slugs from manifest: embedded == False and failed_at_step starts with "embedded"
            slugs_to_retry = []
            for slug, info in st.data.items():
                if not info.get("embedded", False) and (
                    info.get("failed_at_step", "") if info.get("failed_at_step") else ""
                ).startswith("embedded"):
                    slugs_to_retry.append(slug)
            print(f"Loaded {len(slugs_to_retry)} slugs from manifest for retry.")

        if not slugs_to_retry:
            print("No slugs to retry.")
            return

        chunks = []
        for slug in tqdm(slugs_to_retry, desc="Retrying failed embeddings"):
            tk = TranscriptKey.from_slug(slug)
            html_path = tk.to_path(data_root="data")

            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    parser = Parser.from_html(f.read(), tk, st.get_url(tk.slug()))
                    chunks.extend(parser.parse_html())
                if not args.dry_run:
                    st.mark_success(tk.slug(), "parsed")
                else:
                    print(f"🚫 Dry run: Would have marked {slug} as parsed.")
            except Exception as e:
                if not args.dry_run:
                    st.mark_failure(tk.slug(), "parsed", str(e))
                else:
                    print(f"🚫 Dry run: Would have marked {slug} as failed.\n{e}")

        processor = ChunkProcessor(chunks)
        if not args.dry_run:
            processor.embed()
            processor.upsert()
            for slug in processor.get_successful_slugs():
                st.mark_success(slug, "embedded")
            for slug in processor.get_failed_slugs():
                st.mark_failure(slug, "embedded", "Embedding or upsert failed")
            st.save()
            save_skipped_slugs(processor.get_failed_slugs(), reason="embedding")
        else:
            print(f"🚫 Dry run: Would have embedded and upserted {len(chunks)} chunks.")
            for slug in processor.get_successful_slugs():
                print(f"🚫 Dry run: Would have marked {slug} as embedded success.")
            for slug in processor.get_failed_slugs():
                print(f"🚫 Dry run: Would have marked {slug} as embedded failure.")
        report = processor.get_report()
        save_ingest_report(report, args.step)

    elif args.step == "refresh_metadata":

        chunks = []
        slugs_to_refresh = st.filter_for(step="html_saved", status=True)

        for slug in tqdm(slugs_to_refresh, desc="Re-parsing HTML for metadata refresh"):
            tk = TranscriptKey.from_slug(slug)
            html_path = tk.to_path(data_root="data")
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    parser = Parser.from_html(f.read(), tk, st.get_url(tk.slug()))
                    chunks.extend(parser.parse_html())
            except Exception as e:
                print(f"⚠️ Failed to parse {slug}: {e}")

        processor = ChunkProcessor(chunks)
        asyncio.run(processor.refresh_metadata_async(dry_run=args.dry_run))

    elif args.step == "extract_candidates":
        from collections import Counter
        from utils.text_util import split_sentences

        counts = Counter()
        slug_url_pairs = [(slug, st.get_url(slug)) for slug in st.data.keys()]

        def _process_transcript(pair):
            slug, url = pair
            tk = TranscriptKey.from_slug(slug)
            html_path = tk.to_path(data_root="data")
            local_counter = Counter()
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    parser = Parser.from_html(f.read(), tk, url)
                    chunks = parser.parse_html()
            except Exception as e:
                return local_counter
            for chunk in chunks:
                for sent in split_sentences(chunk.text):
                    norm = sent.strip().rstrip(".!?").lower()
                    if len(norm.split()) <= 5:
                        local_counter[norm] += 1
            return local_counter

        max_workers = min(32, (os.cpu_count() or 1) + 4)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [
                pool.submit(_process_transcript, pair) for pair in slug_url_pairs
            ]
            for fut in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="🔍 Scanning transcripts for filler candidate sentences...",
            ):
                counts.update(fut.result())

        # Finally, print your top candidates
        print("\nTop filler candidates (count ≥ 20):")
        for sentence, cnt in counts.most_common():
            if cnt < 20:
                break
            print(f"{cnt:4d}  {sentence}")

    elif args.step == "regenerate_snippets":
        from utils.text_util import generate_snippet

        # File to record chunks that are all filler
        filler_log = open("data/all_filler_chunks.txt", "w", encoding="utf-8")
        all_chunks = []

        def process_slug(slug):
            tk = TranscriptKey.from_slug(slug)
            html_path = tk.to_path(data_root="data")
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    parser = Parser.from_html(f.read(), tk, st.get_url(slug))
                    chunks = parser.parse_html()
            except Exception as e:
                return []
            for chunk in chunks:
                snippet = generate_snippet(chunk.text)
                # attach regenerated snippet
                chunk.snippet = snippet
                if not snippet:
                    # log slug and chunk identifier
                    filler_log.write(
                        f"{slug}\t{chunk.primary_speakers[0]}\t{chunk.chunk_id}\n"
                    )
            return chunks

        # Multithread processing
        slugs = list(st.data.keys())
        max_workers = min(32, (os.cpu_count() or 1) + 4)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(process_slug, slug) for slug in slugs]
            for fut in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="Regenerating snippets",
            ):
                all_chunks.extend(fut.result())

        filler_log.close()

        # Refresh metadata with new snippets
        processor = ChunkProcessor(all_chunks)
        asyncio.run(processor.refresh_metadata_async(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
