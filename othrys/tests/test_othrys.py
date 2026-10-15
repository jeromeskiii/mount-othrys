import json
from pathlib import Path
import pytest

from othrys.config import DEFAULT_MODEL, DEFAULT_TIMEOUT
from othrys.types import LLMConfig, AgentRunResult, ToolCallRecord
from othrys.tools import (
    ToolContext,
    _truncate,
    _resolve,
    _under_workdir,
    _safe_env,
    tool_specs,
    make_dispatcher,
)
from othrys.cli_helpers import print_obj, handle_cli_errors, add_common_args
import argparse


def test_truncate():
    short = "hello world"
    assert _truncate(short, 100) == short

    long_str = "a" * 100
    res = _truncate(long_str, 20)
    assert "[... 80 chars truncated ...]" in res


def test_path_resolution_and_traversal_guard(tmp_path: Path):
    ctx = ToolContext(workdir=tmp_path)
    p = _resolve(ctx, "sub/file.txt")
    assert p == (tmp_path / "sub" / "file.txt").resolve()
    assert _under_workdir(ctx, p) is True

    outside = tmp_path.parent / "outside.txt"
    assert _under_workdir(ctx, outside) is False


def test_tool_specs():
    specs = tool_specs()
    names = {s["name"] for s in specs}
    assert "bash" in names
    assert "read" in names
    assert "write" in names
    assert "edit" in names
    assert "list_dir" in names


def test_tool_dispatcher(tmp_path: Path):
    ctx = ToolContext(workdir=tmp_path)
    dispatch = make_dispatcher(ctx)

    # 1. Write tool
    out, is_err = dispatch("write", {"path": "test.txt", "content": "line1\nline2\n"})
    assert not is_err
    assert (tmp_path / "test.txt").exists()

    # 2. Read tool
    out, is_err = dispatch("read", {"path": "test.txt"})
    assert not is_err
    assert out == "line1\nline2\n"

    # 3. Edit tool
    out, is_err = dispatch("edit", {"path": "test.txt", "old_string": "line1", "new_string": "alpha"})
    assert not is_err
    assert (tmp_path / "test.txt").read_text() == "alpha\nline2\n"

    # 4. List tool
    out, is_err = dispatch("list_dir", {"path": "."})
    assert not is_err
    assert "test.txt" in out

    # 5. Outside directory write refusal
    out, is_err = dispatch("write", {"path": "../secret.txt", "content": "bad"})
    assert is_err
    assert "Refused" in out

    # 5b. Outside directory list refusal
    out, is_err = dispatch("list_dir", {"path": ".."})
    assert is_err
    assert "Refused" in out

    # 6. Bash tool with chaining
    out, is_err = dispatch("bash", {"command": "echo 'first' && echo 'second' | grep 'second'"})
    assert not is_err
    assert "second" in out

    # 7. Unknown tool
    out, is_err = dispatch("unknown_tool", {})
    assert is_err
    assert "Unknown tool" in out


def test_cli_helpers(capsys):
    data = {"status": "ok", "count": 42}
    print_obj(data, as_json=True)
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["status"] == "ok"

    parser = argparse.ArgumentParser()
    add_common_args(parser)
    args = parser.parse_args(["--json", "--workdir", "/tmp"])
    assert args.json is True
    assert args.workdir == "/tmp"

    @handle_cli_errors
    def failing_fn():
        raise FileNotFoundError("missing file")

    exit_code = failing_fn()
    assert exit_code == 1
