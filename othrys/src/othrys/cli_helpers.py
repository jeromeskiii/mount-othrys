import json
import sys
from argparse import ArgumentParser
from typing import Any, Callable


def print_obj(obj: Any, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, default=str))
    else:
        print(obj)


def add_common_args(parser: ArgumentParser, *, with_api_key: bool = True) -> None:
    parser.add_argument("--json", action="store_true", help="output as JSON")
    parser.add_argument("--root", default=None, help="project root directory")
    parser.add_argument("--workdir", default=".", help="working directory")
    parser.add_argument("--model", default=None, help="model to use")
    if with_api_key:
        parser.add_argument("--api-key", default=None, help="Anthropic API key")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")


def handle_cli_errors(main_fn: Callable[[], int]) -> Callable[[], int]:
    def wrapper() -> int:
        try:
            return main_fn()
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    return wrapper
