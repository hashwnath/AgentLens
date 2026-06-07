#!/usr/bin/env bash
# Launch the Kronos Web UI on http://localhost:7070
set -e

KRONOS_DIR="$(dirname "$(realpath "$0")")/../.kronos-src"

if [ ! -d "$KRONOS_DIR" ]; then
    echo "Kronos not set up yet. Run: bash $(dirname "$0")/setup.sh"
    exit 1
fi

echo "Starting Kronos Web UI at http://localhost:7070 ..."
cd "$KRONOS_DIR/webui"
python app.py
