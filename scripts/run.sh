#!/bin/bash
# Run the MCP server from the plugin's venv.
set -e

PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
VENV_DIR="$PLUGIN_DIR/.venv"

# Auto-setup on first run
if [ ! -d "$VENV_DIR" ]; then
    bash "$PLUGIN_DIR/scripts/setup.sh"
fi

exec "$VENV_DIR/bin/python" -m advanced_prompting_engine
