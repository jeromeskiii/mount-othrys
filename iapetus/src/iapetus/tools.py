from pathlib import Path
from typing import Any

from othrys import ToolContext, make_dispatcher as _make_othrys_dispatcher, tool_specs as _othrys_tool_specs

tool_specs = _othrys_tool_specs

def make_dispatcher(*, workdir: Path) -> Any:
    ctx = ToolContext(workdir=workdir)
    return _make_othrys_dispatcher(ctx)
