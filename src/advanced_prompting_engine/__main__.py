"""Entry point for the MCP server.

Usage:
    python -m advanced_prompting_engine
    uvx advanced-prompting-engine
"""

import logging
import sys

from advanced_prompting_engine.server import create_server


def main():
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
