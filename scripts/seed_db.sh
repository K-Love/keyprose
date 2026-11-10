#!/usr/bin/env bash
# seed_db.sh — Create a local SQLite file of sample rows.
# The running app does not open this file.
# Usage: bash scripts/seed_db.sh
#
# Default filename: keyprose.db
# If DB_FILE is unset, keyprose.db is missing, and listing_pilot.db exists,
# the older filename is updated instead of starting a second file.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ -z "${DB_FILE:-}" ]; then
  if [ -f "$REPO_ROOT/keyprose.db" ]; then
    DB_FILE="keyprose.db"
  elif [ -f "$REPO_ROOT/listing_pilot.db" ]; then
    DB_FILE="listing_pilot.db"
    echo "Using existing listing_pilot.db."
    echo "New databases are named keyprose.db. Set DB_FILE to choose a file."
  else
    DB_FILE="keyprose.db"
  fi
fi

echo "Seeding demo database: $DB_FILE"

if ! command -v sqlite3 &>/dev/null; then
  echo "sqlite3 is required. Install it with your system package manager."
  exit 1
fi

sqlite3 "$DB_FILE" < backend/data/seed_demo_data.sql

echo "Database seeded."
echo ""
echo "Tables created:"
sqlite3 "$DB_FILE" ".tables"
echo ""
echo "Sample data:"
echo "  Properties: $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM properties;')"
echo "  Contacts:   $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM contacts;')"
echo "  Campaigns:  $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM campaigns;')"
