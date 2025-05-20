#!/usr/bin/env bash
set -euo pipefail

# Install Python dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r backend/requirements.txt
python3 -m pip install -r scraper/requirements.txt
python3 -m pip install -e .

# Install frontend dependencies
cd frontend && npm ci && cd ..


