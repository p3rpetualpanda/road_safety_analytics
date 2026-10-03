# Road Safety Analytics — convenience commands
# Usage: make <target>
#
# Set DB_URL to your connection string, e.g.:
#   make load DB_URL="postgresql://postgres:postgres@localhost:5432/road_safety"

DB_URL ?= postgresql://postgres:postgres@localhost:5432/road_safety
DATA_DIR ?= data

.PHONY: setup schema load verify clean help

help:
	@echo "Road Safety Analytics — available targets:"
	@echo "  make setup   - create the database (requires createdb)"
	@echo "  make schema  - apply sql/schema.sql"
	@echo "  make load    - run the ETL (idempotent)"
	@echo "  make verify  - print row counts for each table"
	@echo "  make clean   - truncate all warehouse tables"
	@echo ""
	@echo "Example:"
	@echo "  make load DB_URL=\"postgresql://user:pass@localhost:5432/road_safety\""

setup:
	createdb road_safety || echo "Database may already exist."

schema:
	psql "$(DB_URL)" -f sql/schema.sql

load:
	python etl/load.py --data-dir "$(DATA_DIR)" --db-url "$(DB_URL)"

verify:
	@echo "=== Row counts ==="
	psql "$(DB_URL)" -c "SELECT 'dim_date' AS tbl, COUNT(*) FROM dim_date UNION ALL SELECT 'dim_location', COUNT(*) FROM dim_location UNION ALL SELECT 'fact_accident', COUNT(*) FROM fact_accident UNION ALL SELECT 'fact_casualty', COUNT(*) FROM fact_casualty UNION ALL SELECT 'fact_vehicle', COUNT(*) FROM fact_vehicle;"

clean:
	psql "$(DB_URL)" -c "TRUNCATE fact_vehicle, fact_casualty, fact_accident, dim_location, dim_date RESTART IDENTITY CASCADE;"
