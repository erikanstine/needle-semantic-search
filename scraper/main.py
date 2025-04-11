import argparse
import json

from crawler_manager import get_urls_and_store
from scraper_manager import run_scraper_manager

from utils.report import print_run_report, save_run_report


def main():
    parser = argparse.ArgumentParser(description="Transcript Ingestion Pipeline")
    parser.add_argument(
        "step",
        choices=["crawl", "scrape", "ingest", "batch_ingest"],
        help="Which step to run: 'crawl' (discover URLs), 'scrape' (ingest known URLs), 'ingest' (crawl + scrape), or 'batch_ingest' (ingest in batches)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scraping URLs even if already marked as scraped",
    )
    args = parser.parse_args()

    if args.step == "crawl":
        urls = get_urls_and_store(force=args.force)
        if not urls:
            print("No new transcripts found.")
        else:
            print(f"Discovered {len(urls)} new transcript URLs.")

    elif args.step == "scrape":
        try:
            with open("data/urls_to_scrape.json") as f:
                url_list = json.load(f)
            report = run_scraper_manager(url_list, force=args.force)
            print_run_report(report)
            save_run_report(report)
        except FileNotFoundError:
            print("No cached URL list found. Run 'crawl' or 'ingest' first.")

    elif args.step == "ingest":
        urls = get_urls_and_store(force=args.force)
        if not urls:
            print("No new transcripts found.")
            return
        print(f"Discovered {len(urls)} new transcript URLs.")
        report = run_scraper_manager(urls, force=args.force)
        print_run_report(report)
        save_run_report(report)
    elif args.step == "batch_ingest":
        urls = get_urls_and_store(force=args.force)
        if not urls:
            print("No new transcripts found.")
            return
        print(f"Discovered {len(urls)} new transcript URLs.")
        report = run_scraper_manager(urls, force=args.force, batch=True)
        print_run_report(report)
        save_run_report(report)


if __name__ == "__main__":
    main()
