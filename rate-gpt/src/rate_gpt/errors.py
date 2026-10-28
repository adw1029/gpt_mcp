"""Domain errors. Services raise these; the tool layer turns them into MCP tool errors."""
from contextlib import contextmanager

from mcp.server.mcpserver.exceptions import ToolError


class AppError(Exception):
    """An expected failure whose message is safe to show the model and the user."""


class NotFoundError(AppError):
    pass


class InvalidStateError(AppError):
    pass


class IntegrationError(AppError):
    """A downstream system failed. Details go to the logs; the message stays generic."""


@contextmanager
def as_tool_errors():
    """Re-raise AppError as ToolError so the model sees the message, not a crash."""
    try:
        yield
    except AppError as exc:
        raise ToolError(str(exc)) from exc
