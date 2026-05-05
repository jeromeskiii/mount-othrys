# Othrys — Shared Titan Core Library

Shared Python library providing the foundational types, LLM client, tool runtime, and CLI helpers for all Mount Othrys Titans.

## Modules

| Module | Purpose |
|--------|---------|
| `othrys.config` | `load_env()`, default constants (model, tokens, temperature, timeout) |
| `othrys.types` | `LLMConfig`, `ToolCallRecord`, `AgentRunResult` dataclasses |
| `othrys.llm` | `BaseLLM` — unified Anthropic agent loop with ephemeral caching, adaptive thinking, and tool dispatch |
| `othrys.tools` | `tool_specs()` + `make_dispatcher()` — bash, read, write, edit, list_dir with sandbox enforcement |
| `othrys.cli_helpers` | `print_obj()`, `add_common_args()`, `handle_cli_errors()` — argparse boilerplate |

## Usage

```python
from othrys import BaseLLM, LLMConfig, ToolContext, make_dispatcher, tool_specs

class MyLLM(BaseLLM):
    def __init__(self, config=None):
        super().__init__(config or LLMConfig(max_tokens=64000))

ctx = ToolContext(workdir=".")
dispatch = make_dispatcher(ctx)

result = MyLLM().run_agent(
    system="You are a helpful assistant.",
    user_prompt="List all Python files.",
    tools=tool_specs(),
    tool_dispatch=dispatch,
)
```

## Dependency DAG

```
othrys (anthropic, pyyaml, python-dotenv)
  ▲
  ├── atlas     → depends on othrys
  ├── coeus     → depends on othrys
  ├── iapetus   → depends on othrys, atlas
  ├── talos     → depends on othrys, atlas, iapetus
  └── kronos    → depends on othrys, atlas, iapetus, talos, coeus
```
