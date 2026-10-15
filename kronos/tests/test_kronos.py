from pathlib import Path

from kronos.config import load_config
from kronos.dispatch import build_dispatch_plan
from kronos.registry import TitanDomain, TitanMode, get_titan, list_titans
from kronos.router import route, route_explicit


def test_registry_lookup():
    coeus = get_titan("coeus")
    assert coeus.name == "coeus"
    assert coeus.domain == TitanDomain.PLANNING
    assert coeus.cli_command == "coeus"

    atlas = get_titan("atlas")
    assert atlas.cli_command == "atlas"

    iapetus = get_titan("iapetus")
    assert iapetus.thinking_budget == 32_000


def test_registry_legacy_aliases():
    assert get_titan("sisyphus").name == "talos"
    assert get_titan("prometheus").name == "coeus"
    assert get_titan("oracle").name == "themis"
    assert get_titan("hephaestus").name == "iapetus"
    assert get_titan("ultrawork").name == "heracles"


def test_registry_unknown_raises():
    try:
        _ = get_titan("nonexistent")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass


def test_list_titans():
    titans = list_titans()
    assert len(titans) == 7
    names = {t.name.lower() for t in titans}
    assert names == {"coeus", "atlas", "iapetus", "talos", "themis", "heracles", "coordinator"}


def test_route_planning():
    titan, _ = route("plan this feature for me")
    assert titan.mode == TitanMode.COEUS


def test_route_atlas():
    titan, _ = route("run the atlas boulder")
    assert titan.mode == TitanMode.ATLAS


def test_route_deep():
    titan, _ = route("deep analyze the codebase")
    assert titan.mode == TitanMode.IAPETUS


def test_route_themis():
    titan, _ = route("consult on this architecture decision")
    assert titan.mode == TitanMode.THEMIS


def test_route_heracles():
    titan, _ = route("ultrawork finish this entire feature now")
    assert titan.mode == TitanMode.HERACLES


def test_route_default():
    titan, _ = route("fix the bug in auth.py")
    assert titan.mode == TitanMode.TALOS


def test_config_defaults():
    config = load_config(Path("/nonexistent/kronos.yaml"))
    assert config.default_model == "claude-sonnet-4-5"
    assert config.thinking_budget == 32_000
    assert config.max_tokens == 64_000
    assert config.timeout == 600


def test_route_explicit():
    titan = route_explicit("atlas")
    assert titan.cli_command == "atlas"

    titan = route_explicit("themis")
    assert titan.cli_command == "kronos"


def test_dispatch_plan_coeus_default():
    plan = build_dispatch_plan("coeus", "plan this feature")
    assert plan.command == "coeus"
    assert plan.args == ["interview", "plan this feature"]


def test_dispatch_plan_coeus_explicit_args_passthrough():
    plan = build_dispatch_plan("coeus", "plan this feature", ["continue", "draft-123"])
    assert plan.command == "coeus"
    assert plan.args == ["continue", "draft-123"]


def test_dispatch_plan_talos_default():
    plan = build_dispatch_plan("talos", "fix the bug")
    assert plan.command == "talos"
    assert plan.args == ["ask", "fix the bug"]


def test_dispatch_plan_iapetus_default():
    plan = build_dispatch_plan("iapetus", "implement this complex feature")
    assert plan.command == "iapetus"
    assert plan.args == ["execute", "--objective", "implement this complex feature"]


def test_dispatch_plan_themis_is_wired_via_analysis():
    plan = build_dispatch_plan("themis", "consult on this architecture")
    assert plan.command == "iapetus"
    assert plan.args == ["analyze", "--objective", "consult on this architecture"]


def test_dispatch_plan_themis_explicit_args_passthrough():
    plan = build_dispatch_plan("themis", "consult on this architecture", ["execute", "--objective", "override"])
    assert plan.command == "iapetus"
    assert plan.args == ["execute", "--objective", "override"]


def test_dispatch_plan_heracles_is_wired_via_high_intensity_execution():
    plan = build_dispatch_plan("heracles", "finish this now")
    assert plan.command == "iapetus"
    assert plan.args == [
        "execute",
        "--objective",
        "HERACLES MODE ENABLED! finish this now",
        "--max-iterations",
        "80",
    ]


def test_dispatch_plan_heracles_explicit_args_passthrough():
    plan = build_dispatch_plan("heracles", "finish this now", ["analyze", "--objective", "override"])
    assert plan.command == "iapetus"
    assert plan.args == ["analyze", "--objective", "override"]


def test_dispatch_plan_atlas_requires_args():
    try:
        _ = build_dispatch_plan("atlas", "run the boulder")
        assert False, "Atlas should require explicit args"
    except ValueError:
        pass


def test_dispatch_plan_coordinator_delegates_to_talos():
    plan = build_dispatch_plan("coordinator", "coordinate the deployment")
    assert plan.command == "talos"
    assert plan.args == ["ask", "coordinate the deployment"]


def test_dispatch_plan_coordinator_explicit_args_passthrough():
    plan = build_dispatch_plan("coordinator", "coordinate", ["ask", "--json", "hello"])
    assert plan.command == "talos"
    assert plan.args == ["ask", "--json", "hello"]
