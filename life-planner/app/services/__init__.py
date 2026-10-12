"""The service layer: the only code that changes data.

REST routes (app/api) and MCP tools (app/mcp_server.py) are thin wrappers around these
functions, so the dashboard and the AI always behave identically.
"""


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass
