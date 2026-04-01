#!/bin/bash
# Setup script for the advanced-prompting-engine plugin.
# Creates a venv in the plugin root and installs dependencies.
set -e

PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
VENV_DIR="$PLUGIN_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up advanced-prompting-engine..." >&2
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q "$PLUGIN_DIR"
    echo "Setup complete." >&2
fi
