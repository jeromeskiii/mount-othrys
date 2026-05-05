from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

DEFAULT_CONFIG_PATH = Path.cwd() / ".sisyphus" / "kronos.yaml"
KRONOS_HOME = Path.home() / ".sisyphus" / "kronos"


def _load_env() -> None:
    _ = load_dotenv(Path.cwd() / ".env", override=False)
    _ = load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=False)


@dataclass
class KronosConfig:
    default_model: str = "claude-sonnet-4-5"
    api_key: str | None = None
    thinking_budget: int = 32_000
    max_tokens: int = 64_000
    timeout: int = 600
    workdir: str = "."
    titan_overrides: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.titan_overrides is None:
            self.titan_overrides = {}


def load_config(path: Path | None = None) -> KronosConfig:
    _load_env()
    config_path = path or DEFAULT_CONFIG_PATH
    data: dict[str, Any] = {}
    if config_path.exists():
        with open(config_path) as f:
            loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                data = loaded

    api_key = (
        data.get("api_key")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("KRONOS_API_KEY")
    )

    titan_overrides = data.get("titan_overrides", {})
    if not isinstance(titan_overrides, dict):
        titan_overrides = {}

    return KronosConfig(
        default_model=str(data.get("default_model", "claude-sonnet-4-5")),
        api_key=api_key,
        thinking_budget=int(data.get("thinking_budget", 32_000)),
        max_tokens=int(data.get("max_tokens", 64_000)),
        timeout=int(data.get("timeout", 600)),
        workdir=str(data.get("workdir", ".")),
        titan_overrides=titan_overrides,
    )


def save_config(config: KronosConfig, path: Path | None = None) -> None:
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "default_model": config.default_model,
        "thinking_budget": config.thinking_budget,
        "max_tokens": config.max_tokens,
        "timeout": config.timeout,
        "workdir": config.workdir,
    }
    # API key is never persisted to disk — load from environment only.
    if config.titan_overrides:
        data["titan_overrides"] = config.titan_overrides
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
