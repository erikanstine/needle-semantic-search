import argparse

from tqdm import tqdm

from chunk_processor import ChunkProcessor
from crawler_manager import get_urls_and_store
from html_fetcher import HTMLFetcher
from parser import Parser
from status_tracker import StatusTracker
from ingest import ingest_chunks

from utils.report import (
    print_run_report,
    save_run_report,
    save_skipped_slugs,
    save_ingest_report,
)
from utils.storage import TranscriptKey


def main():
    st = StatusTracker()
    parser = argparse.ArgumentParser(description="Transcript Ingestion Pipeline")
    parser.add_argument(
        "step",
        choices=[
            "crawl",
            "fetch",
            "ingest",
            "retry",
        ],
        help="Step to run: 'crawl' (discover URLs), 'fetch' (download HTML), 'ingest' (parse and embed), or 'retry' (retry failed embeddings)",
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
                url_list = f.read()
            fetcher = HTMLFetcher(st, url_list, force=args.force)
            fetcher.fetch()
            report = fetcher.get_report()
            print_run_report(report)
            save_run_report(report)
        except FileNotFoundError:
            print("No cached URL list found. Run 'crawl' first.")

    elif args.step == "ingest":
        chunks = []
        slugs_to_parse = st.filter_for(step="parsed", status=False)
        for slug in tqdm(slugs_to_parse, desc="Parsing transcripts"):
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


if __name__ == "__main__":
    main()
