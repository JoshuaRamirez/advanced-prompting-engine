"""Entry point for the MCP server.

Usage:
    python -m advanced_prompting_engine
    uvx advanced-prompting-engine
"""

from advanced_prompting_engine.server import create_server


def main():
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
