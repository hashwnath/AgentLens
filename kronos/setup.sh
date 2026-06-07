#!/usr/bin/env bash
# Kronos setup script — clones the repo and installs all dependencies.
set -e

KRONOS_DIR="$(dirname "$(realpath "$0")")/../.kronos-src"

echo "Setting up Kronos financial model..."

# Clone if not already present
if [ ! -d "$KRONOS_DIR" ]; then
    git clone https://github.com/shiyu-coder/Kronos.git "$KRONOS_DIR"
    echo "Cloned Kronos to $KRONOS_DIR"
else
    echo "Kronos source already present at $KRONOS_DIR"
fi

# Install dependencies
pip install -r "$KRONOS_DIR/requirements.txt"
pip install -r "$KRONOS_DIR/webui/requirements.txt"

echo ""
echo "Done. Run the Web UI with:"
echo "  bash $(dirname "$0")/start_webui.sh"
