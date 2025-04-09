from crawler import get_new_transcript_urls
from scraper_manager import run_scraper_manager


def main():
    # Step 1: Crawl and discover new URLs
    new_urls = get_new_transcript_urls()
    if not new_urls:
        print("No new transcripts found.")
        return

    # Step 2: Process new URLs
    run_scraper_manager(new_urls)


if __name__ == "__main__":
    main()
