"""
Output formatting utilities for the monitorpy package.
"""
import json
from typing import Any
import datetime

from monitorpy.core import CheckResult


class ColorFormatter:
    """Utility class for adding color to terminal output."""

    # ANSI color codes
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def success(cls, text: str) -> str:
        """Format text as success (green)."""
        return f"{cls.GREEN}{text}{cls.RESET}"

    @classmethod
    def warning(cls, text: str) -> str:
        """Format text as warning (yellow)."""
        return f"{cls.YELLOW}{text}{cls.RESET}"

    @classmethod
    def error(cls, text: str) -> str:
        """Format text as error (red)."""
        return f"{cls.RED}{text}{cls.RESET}"

    @classmethod
    def info(cls, text: str) -> str:
        """Format text as info (blue)."""
        return f"{cls.BLUE}{text}{cls.RESET}"

    @classmethod
    def highlight(cls, text: str) -> str:
        """Format text as highlighted (bold)."""
        return f"{cls.BOLD}{text}{cls.RESET}"


def format_result(result: CheckResult, verbose: bool = False) -> str:
    """
    Format a check result for display.

    Args:
        result: The check result to format
        verbose: Whether to include detailed information

    Returns:
        str: Formatted result string
    """
    status_formatters = {
        CheckResult.STATUS_SUCCESS: ColorFormatter.success,
        CheckResult.STATUS_WARNING: ColorFormatter.warning,
        CheckResult.STATUS_ERROR: ColorFormatter.error
    }

    formatter = status_formatters.get(result.status, str)
    status_str = formatter(result.status.upper())

    output = [
        f"{status_str}: {result.message}",
        f"Response time: {result.response_time:.4f} seconds"
    ]

    if verbose:
        output.append("\nRaw data:")
        output.append(json.dumps(result.raw_data, indent=2, cls=JSONEncoder))

    return "\n".join(output)


class JSONEncoder(json.JSONEncoder):
    """Extended JSON encoder that can handle dates, times, and other complex types."""

    def default(self, obj: Any) -> Any:
        """Serialize additional types to JSON."""
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            return obj.to_dict()
        elif hasattr(obj, "__str__"):
            return str(obj)
        return super().default(obj)
