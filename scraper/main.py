import argparse
import json


from crawler import get_new_transcript_urls
from scraper_manager import run_scraper_manager


def main():
    parser = argparse.ArgumentParser(description="Transcript Ingestion Pipeline")
    parser.add_argument(
        "step",
        choices=["crawl", "scrape", "ingest"],
        help="Which step to run: 'crawl' (discover URLs), 'scrape' (ingest known URLs), or 'ingest' (crawl + scrape)",
    )
    args = parser.parse_args()

    if args.step == "crawl":
        urls = get_new_transcript_urls()
        if not urls:
            print("No new transcripts found.")
        else:
            print(f"Discovered {len(urls)} new transcript URLs.")

    elif args.step == "scrape":
        try:
            with open("data/urls_to_scrape.json") as f:
                url_list = json.load(f)
            run_scraper_manager(url_list)
        except FileNotFoundError:
            print("No cached URL list found. Run 'crawl' or 'ingest' first.")
        run_scraper_manager(url_list)

    elif args.step == "ingest":
        new_urls = get_new_transcript_urls()
        if not new_urls:
            print("No new transcripts found.")
            return
        run_scraper_manager(new_urls)


if __name__ == "__main__":
    main()
