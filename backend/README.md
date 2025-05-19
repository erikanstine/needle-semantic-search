## Backend
- FastAPI running via Uvicorn
- Hosted by fly.io
- GH Action triggers fly.io deploy
    - Configuration to trigger deploy without waiting on a fly.io build machine (took much trial and error):
    `flyctl deploy --depot=false`
- Exposes `/healthz` endpoint for uptime monitoring.
