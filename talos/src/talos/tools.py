from typing import Any

from othrys import ToolContext, make_dispatcher as _make_othrys_dispatcher, tool_specs as _othrys_tool_specs


def make_dispatcher(*, workdir=None) -> Any:
    from pathlib import Path
    wd = Path(workdir) if workdir else Path.cwd()
    ctx = ToolContext(workdir=wd)
    return _make_othrys_dispatcher(ctx)


def tool_specs() -> list[dict[str, Any]]:
    return _othrys_tool_specs()
