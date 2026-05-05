from pathlib import Path

from dotenv import load_dotenv


DEFAULT_MODEL = "claude-opus-4-5"
DEFAULT_THINKING_BUDGET = 32_000
DEFAULT_MAX_TOKENS = 48_000
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_ITERATIONS = 50
DEFAULT_TIMEOUT = 600


def load_env() -> None:
    load_dotenv(Path.cwd() / ".env", override=False)
    pkg_env = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(pkg_env, override=False)
