#!/bin/bash
# Cron ETL: 0 2 * * * /path/to/scripts/run_etl_cron.sh
cd "$(dirname "$0")/.."
source .venv/bin/activate
python scripts/recreate_dataset_view.py
python main.py >> logs/etl_cron.log 2>&1
