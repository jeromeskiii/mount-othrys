from dataclasses import dataclass, field

from .config import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_THINKING_BUDGET


@dataclass
class LLMConfig:
    model: str = DEFAULT_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    thinking_budget: int = DEFAULT_THINKING_BUDGET
    temperature: float = DEFAULT_TEMPERATURE
    api_key: str | None = None


@dataclass
class ToolCallRecord:
    name: str
    input: dict
    result: str
    is_error: bool = False


@dataclass
class AgentRunResult:
    final_text: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    stop_reason: str = ""
    iterations: int = 0
    thinking_content: list[str] = field(default_factory=list)
