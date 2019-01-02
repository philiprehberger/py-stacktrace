"""Turn Python stack traces into cleaner, more readable output."""

from __future__ import annotations

import linecache
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any


__all__ = [
    "install",
    "format_exception",
    "ExceptionReport",
    "FrameInfo",
]

# ANSI colors
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_CYAN = "\033[36m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


@dataclass
class FrameInfo:
    """Information about a single stack frame."""

    filename: str
    lineno: int
    function: str
    line: str
    is_stdlib: bool = False

    @property
    def short_filename(self) -> str:
        """Filename relative to cwd or shortened."""
        try:
            return str(Path(self.filename).relative_to(Path.cwd()))
        except ValueError:
            return self.filename


@dataclass
class ExceptionReport:
    """Formatted exception information."""

    exc_type: str
    message: str
    frames: list[FrameInfo] = field(default_factory=list)
    cause: ExceptionReport | None = None

    def short(self) -> str:
        """One-line summary of the exception."""
        if self.frames:
            f = self.frames[-1]
            return f"{self.exc_type}: {self.message} ({f.short_filename}:{f.lineno} in {f.function})"
        return f"{self.exc_type}: {self.message}"

    def detailed(self, *, color: bool = True, context: int = 2, hide_stdlib: bool = True) -> str:
        """Detailed formatted output with source context.

        Args:
            color: Enable ANSI color output.
            context: Number of context lines around the error.
            hide_stdlib: Hide standard library and site-packages frames.

        Returns:
            Formatted string.
        """
        lines: list[str] = []

        if self.cause:
            lines.append(self.cause.detailed(color=color, context=context, hide_stdlib=hide_stdlib))
            header = "During handling of the above exception, another exception occurred:"
            if color:
                header = f"{_DIM}{header}{_RESET}"
            lines.append(f"\n{header}\n")

        # Exception header
        header = f"{self.exc_type}: {self.message}"
        if color:
            header = f"{_BOLD}{_RED}{header}{_RESET}"
        lines.append(header)
        lines.append("")

        # Frames (reversed: most recent last, but we show most recent first)
        visible = self.frames
        if hide_stdlib:
            user_frames = [f for f in visible if not f.is_stdlib]
            if user_frames:
                visible = user_frames

        hidden_count = len(self.frames) - len(visible)
        if hidden_count > 0:
            note = f"  ({hidden_count} stdlib frames hidden)"
            if color:
                note = f"{_DIM}{note}{_RESET}"
            lines.append(note)

        for frame in visible:
            loc = f"  {frame.short_filename}:{frame.lineno} in {frame.function}"
            if color:
                loc = f"  {_CYAN}{frame.short_filename}{_RESET}:{_YELLOW}{frame.lineno}{_RESET} in {_GREEN}{frame.function}{_RESET}"
            lines.append(loc)

            # Source context
            if context > 0:
                source_lines = _get_context(frame.filename, frame.lineno, context)
                for lno, text, is_current in source_lines:
                    prefix = " >> " if is_current else "    "
                    line_text = f"    {prefix}{lno:4d} | {text}"
                    if color and is_current:
                        line_text = f"    {_BOLD}{_RED}{prefix}{lno:4d} | {text}{_RESET}"
                    elif color:
                        line_text = f"    {_DIM}{prefix}{lno:4d} | {text}{_RESET}"
                    lines.append(line_text)
                lines.append("")

        return "\n".join(lines)


def format_exception(exc: BaseException) -> ExceptionReport:
    """Create an ExceptionReport from an exception.

    Args:
        exc: The exception to format.

    Returns:
        ExceptionReport with frame information.
    """
    cause = None
    if exc.__cause__:
        cause = format_exception(exc.__cause__)

    frames: list[FrameInfo] = []
    tb = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        lineno = tb.tb_lineno
        function = frame.f_code.co_name
        line = linecache.getline(filename, lineno).strip()

        frames.append(FrameInfo(
            filename=filename,
            lineno=lineno,
            function=function,
            line=line,
            is_stdlib=_is_stdlib(filename),
        ))
        tb = tb.tb_next

    return ExceptionReport(
        exc_type=type(exc).__qualname__,
        message=str(exc),
        frames=frames,
        cause=cause,
    )


def install(*, color: bool = True, context: int = 2, hide_stdlib: bool = True) -> None:
    """Install as the global exception handler.

    Replaces ``sys.excepthook`` so all unhandled exceptions are
    formatted with this library.

    Args:
        color: Enable ANSI colors.
        context: Context lines around the error.
        hide_stdlib: Hide stdlib frames.
    """
    def hook(exc_type: type[BaseException], exc_value: BaseException, exc_tb: TracebackType | None) -> None:
        if exc_tb is not None:
            exc_value = exc_value.with_traceback(exc_tb)
        report = format_exception(exc_value)
        print(report.detailed(color=color, context=context, hide_stdlib=hide_stdlib), file=sys.stderr)

    sys.excepthook = hook


def _is_stdlib(filename: str) -> bool:
    normalized = filename.replace("\\", "/").lower()
    return (
        "/lib/python" in normalized
        or "/site-packages/" in normalized
        or "\\lib\\python" in normalized.replace("/", "\\")
        or normalized.startswith("<")
    )


def _get_context(filename: str, lineno: int, context: int) -> list[tuple[int, str, bool]]:
    lines: list[tuple[int, str, bool]] = []
    start = max(1, lineno - context)
    end = lineno + context

    for lno in range(start, end + 1):
        line = linecache.getline(filename, lno)
        if line:
            lines.append((lno, line.rstrip(), lno == lineno))

    return lines
