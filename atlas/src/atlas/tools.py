from othrys import ToolContext, make_dispatcher as _make_dispatcher, tool_specs as _tool_specs

tool_specs = _tool_specs

def make_dispatcher(ctx: ToolContext):
    return _make_dispatcher(ctx)
