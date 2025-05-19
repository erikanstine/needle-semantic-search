# Ingestion Pipeline

Currently implemented as a CLI utility, this tool is used to:
- Crawl for URLs to pull
- Fetch HTML from the URLs
- Parse the HTML
- Ingest parsed HTML
  - Embed (OpenAI API)
  - Upsert (Pinecone Index)

### Crawl
Given a list of tickers (~Fortune 50), pull URLs for earnings transcripts
- Stored timestamps of when no new URLs were most recently found for a given ticker (ie they've all been seen/processed)
- Write new URLs to file

### Fetch
Given a list of transcript URLs, pull down HTML and save to storage
- Storage interface to enable easy swapping out of Local storage for S3 storage or other
- Reduces number of requests by storing HTML (not re-pulling with every ingestion)

### Ingest
Given stored HTML
- Parse into "chunks" of single-speaker prepared remarks, or exchanges within a Q&A session
- Fetch embeddings for chunks in batch (token-aware batching)
- Upload embeddings for chunks in batch to Pinecone DB
