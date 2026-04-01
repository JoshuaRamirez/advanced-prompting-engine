# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please email the maintainer directly:

1. Send a description of the vulnerability to the repository owner via [GitHub private vulnerability reporting](https://github.com/JoshuaRamirez/advanced-prompting-engine/security/advisories/new).
2. Include steps to reproduce, the affected version(s), and any potential impact.
3. Allow reasonable time for a fix before public disclosure (typically 90 days).

## What to Expect

- Acknowledgment of your report within 7 days.
- A plan for resolution or a request for additional information within 14 days.
- Credit in the release notes (unless you prefer to remain anonymous).

## Scope

This project is a single-process MCP server communicating over stdio. It does not listen on network ports, manage authentication tokens, or store user credentials. The primary security surface is:

- **SQLite database writes**: User-extended schema data is persisted locally.
- **Input validation**: Natural language and coordinate inputs are parsed without sandboxing.
- **Dependencies**: NetworkX, numpy, and the MCP SDK are the runtime dependencies.

## Security Best Practices for Users

- Run the server in a restricted environment if processing untrusted input.
- Keep dependencies updated (`pip install --upgrade advanced-prompting-engine`).
- Do not commit `.mcp.json` files containing local filesystem paths to shared repositories.
