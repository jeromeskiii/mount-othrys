from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .boulder_bridge import load_boulder_from_atlas, to_objective, find_blocked_tasks, find_next_pending
from .executor import DeepExecutor, DeepResult
from .llm import DeepLLM, LLMConfig


DEFAULT_MODEL = "claude-opus-4-5"


def _print(obj, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, default=str))
    else:
        print(obj)


def _llm(args) -> DeepLLM:
    return DeepLLM(
        LLMConfig(
            model=args.model,
            api_key=args.api_key,
            thinking_budget=args.thinking_budget,
            max_tokens=args.max_tokens,
        )
    )


def _extract_risk_summary(text: str) -> dict:
    """Extract structured risk summary from Iapetus output."""
    risks = []
    severity_pattern = re.compile(r'\|\s*(.+?)\s*\|\s*(Critical|High|Medium|Low)\s*\|\s*(High|Medium|Low)\s*\|\s*(.+?)\s*\|')
    for match in severity_pattern.finditer(text):
        risks.append({
            "risk": match.group(1).strip(),
            "severity": match.group(2).strip(),
            "likelihood": match.group(3).strip(),
            "mitigation": match.group(4).strip(),
        })

    done_match = re.search(r'DONE:\s*(.+)', text)
    summary = done_match.group(1).strip() if done_match else text[-500:].strip()

    return {"risks": risks, "summary": summary}


def _extract_assessment(text: str) -> dict:
    """Extract assessment verdict from Iapetus output."""
    verdict = "NEEDS_REVISION"
    if "APPROVE_WITH_RISKS" in text.upper():
        verdict = "APPROVE_WITH_RISKS"
    elif "NEEDS_REVISION" in text.upper():
        verdict = "NEEDS_REVISION"
    elif "REJECT" in text.upper():
        verdict = "REJECT"
    return {"verdict": verdict, "analysis": text}


def _extract_stress_result(text: str) -> dict:
    """Extract stress test result from Iapetus output."""
    result = "PASS_WITH_CONCERNS"
    if "STRESS_RESULT: PASS" in text.upper() and "CONCERN" not in text.upper():
        result = "PASS"
    elif "STRESS_RESULT: FAIL" in text.upper():
        result = "FAIL"
    return {"result": result, "analysis": text}


def cmd_analyze(args) -> None:
    llm = _llm(args)
    workdir = Path(args.workdir or args.root).resolve()
    findings = []
    decisions = []
    objective = args.objective or getattr(args, "prompt", None)

    if args.boulder:
        root = Path(args.root).resolve()
        boulder = load_boulder_from_atlas(root=root, name=args.boulder)
        if args.task:
            task = next((t for t in boulder.tasks if t.id == args.task), None)
            if not task:
                _print({"error": f"Task {args.task} not found"}, as_json=args.json)
                sys.exit(1)
            objective = to_objective(boulder=boulder, task=task)
        else:
            objective = boulder.objective
        findings = boulder.findings
        decisions = boulder.decisions

    if not objective:
        _print({"error": "No objective. Provide --objective or --boulder."}, as_json=args.json)
        sys.exit(1)

    from .prompts import RISK_ANALYSIS_SYSTEM, build_analysis_prompt
    prompt = build_analysis_prompt(
        objective=objective,
        workdir=str(workdir),
        findings=findings,
        decisions=decisions,
    )
    analysis = llm.call(
        system=RISK_ANALYSIS_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=args.max_tokens,
    )

    risk_summary = _extract_risk_summary(analysis)

    payload = {
        "objective": objective[:200],
        "analysis": analysis,
        "risks": risk_summary["risks"],
        "top_risk": risk_summary["summary"],
        "model": args.model,
    }
    if args.json:
        _print(payload, as_json=True)
    else:
        print(f"\n=== Risk Analysis ({args.model}) ===\n")
        print(analysis)
        if risk_summary["risks"]:
            print(f"\nTop Risk: {risk_summary['summary']}")
        if args.out:
            Path(args.out).write_text(analysis)
            print(f"\nSaved to {args.out}")


def cmd_assess(args) -> None:
    llm = _llm(args)
    workdir = Path(args.workdir or args.root).resolve()

    plan_path = Path(args.plan).resolve() if args.plan else None
    if not plan_path or not plan_path.exists():
        _print({"error": f"Plan not found: {args.plan}"}, as_json=args.json)
        sys.exit(1)

    plan_content = plan_path.read_text()

    from .prompts import ASSESS_PLAN_SYSTEM, build_assess_prompt
    prompt = build_assess_prompt(
        plan_path=str(plan_path),
        plan_content=plan_content,
        workdir=str(workdir),
    )
    assessment = llm.call(
        system=ASSESS_PLAN_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=args.max_tokens,
    )

    result = _extract_assessment(assessment)

    payload = {
        "plan": str(plan_path),
        "verdict": result["verdict"],
        "analysis": assessment,
        "model": args.model,
    }
    if args.json:
        _print(payload, as_json=True)
    else:
        print(f"\n=== Plan Assessment ({args.model}) ===\n")
        print(assessment)
        print(f"\nVerdict: {result['verdict']}")


def cmd_stress_test(args) -> None:
    llm = _llm(args)
    workdir = Path(args.workdir or args.root).resolve()
    findings = []
    objective = args.objective

    if args.boulder:
        root = Path(args.root).resolve()
        boulder = load_boulder_from_atlas(root=root, name=args.boulder)
        if args.task:
            task = next((t for t in boulder.tasks if t.id == args.task), None)
            if not task:
                _print({"error": f"Task {args.task} not found"}, as_json=args.json)
                sys.exit(1)
            objective = to_objective(boulder=boulder, task=task)
        else:
            objective = boulder.objective
        findings = boulder.findings

    if not objective:
        _print({"error": "No objective. Provide --objective or --boulder."}, as_json=args.json)
        sys.exit(1)

    from .prompts import STRESS_TEST_SYSTEM, build_stress_test_prompt
    prompt = build_stress_test_prompt(
        objective=objective,
        workdir=str(workdir),
        findings=findings,
    )
    analysis = llm.call(
        system=STRESS_TEST_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=args.max_tokens,
    )

    result = _extract_stress_result(analysis)

    payload = {
        "objective": objective[:200],
        "result": result["result"],
        "analysis": analysis,
        "model": args.model,
    }
    if args.json:
        _print(payload, as_json=True)
    else:
        print(f"\n=== Stress Test ({args.model}) ===\n")
        print(analysis)
        print(f"\nResult: {result['result']}")


def cmd_execute(args) -> None:
    """Legacy: deep execution mode (preserved for backward compatibility)."""
    llm = _llm(args)
    workdir = Path(args.workdir or args.root).resolve()
    findings: list[str] = []
    decisions: list[str] = []
    objective = args.objective
    analysis = None

    if args.boulder:
        root = Path(args.root).resolve()
        boulder = load_boulder_from_atlas(root=root, name=args.boulder)
        if args.task:
            task = next((t for t in boulder.tasks if t.id == args.task), None)
            if not task:
                _print({"error": f"Task {args.task} not found"}, as_json=args.json)
                sys.exit(1)
            objective = to_objective(boulder=boulder, task=task)
            if task.notes:
                findings = findings + [f"[{task.id} note] {n}" for n in task.notes]
        else:
            objective = boulder.objective
        findings = findings or boulder.findings
        decisions = boulder.decisions

    if not objective:
        _print({"error": "No objective. Provide --objective or --boulder."}, as_json=args.json)
        sys.exit(1)

    if args.analysis_only:
        executor = DeepExecutor(llm=llm, workdir=workdir)
        analysis = executor.run_analysis(objective=objective, findings=findings, decisions=decisions)
        analysis_payload = {"mode": "analysis_only", "analysis": analysis}
        _print(analysis_payload, as_json=args.json)
        return

    executor = DeepExecutor(llm=llm, workdir=workdir)

    if args.analysis_file:
        analysis = Path(args.analysis_file).read_text()
    result = executor.run(
        objective=objective,
        analysis=analysis,
        findings=findings,
        decisions=decisions,
        max_iterations=args.max_iterations,
        max_tokens=args.max_tokens,
    )

    payload: dict[str, Any] = {
        "success": result.success,
        "blocked": result.blocked,
        "summary": result.summary,
        "iterations": result.iterations,
        "model": args.model,
    }
    if args.json:
        _print(payload, as_json=True)
    else:
        mark = "✓ DONE" if result.success else ("⛔ BLOCKED" if result.blocked else "✗ FAILED")
        print(f"\n\n=== {mark} ({result.iterations} iterations) ===")
        print(result.summary)
        if args.out:
            out = f"# Analysis\n\n{result.analysis}\n\n# Summary\n\n{result.summary}\n"
            Path(args.out).write_text(out)
            print(f"\nSaved to {args.out}")


def main() -> None:
    p = argparse.ArgumentParser(prog="iapetus", description="Iapetus — Risk Analysis Titan from the Mount Othrys system")
    p.add_argument("--version", action="version", version=f"iapetus {__version__}")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--root", default=".", help="project root")
    p.add_argument("--workdir", default=None, help="working directory")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Anthropic model")
    p.add_argument("--api-key", default=None, help="ANTHROPIC_API_KEY override")
    p.add_argument("--thinking-budget", type=int, default=32_000, help="thinking token budget")
    p.add_argument("--max-tokens", type=int, default=48_000, help="max output tokens")

    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("analyze", help="analyze risks, failure modes, and edge cases")
    s.add_argument("prompt", nargs="?", default=None, help="objective to analyze")
    s.add_argument("--objective", default=None, help="objective to analyze")
    s.add_argument("--boulder", default=None, help="atlas boulder name")
    s.add_argument("--task", default=None, help="specific task id within the boulder")
    s.add_argument("--out", default=None, help="write analysis to file")
    s.set_defaults(func=cmd_analyze)

    s = sub.add_parser("assess", help="assess a plan for risks and issues")
    s.add_argument("plan", help="path to the plan file to assess")
    s.set_defaults(func=cmd_assess)

    s = sub.add_parser("stress-test", help="stress-test a system under extreme conditions")
    s.add_argument("--objective", default=None, help="what to stress-test")
    s.add_argument("--boulder", default=None, help="atlas boulder name")
    s.add_argument("--task", default=None, help="specific task id within the boulder")
    s.set_defaults(func=cmd_stress_test)

    s = sub.add_parser("execute", help="deep execution (legacy mode, preserved for backward compatibility)")
    s.add_argument("--objective", default=None, help="raw objective text")
    s.add_argument("--boulder", default=None, help="atlas boulder name")
    s.add_argument("--task", default=None, help="specific task id within the boulder")
    s.add_argument("--analysis-file", default=None, help="skip analysis, use pre-existing analysis file")
    s.add_argument("--analysis-only", action="store_true", help="run analysis phase only, do not execute")
    s.add_argument("--max-iterations", type=int, default=50, help="max agent iterations")
    s.add_argument("--out", default=None, help="write analysis + summary to file")
    s.set_defaults(func=cmd_execute)

    args = p.parse_args()
    try:
        args.func(args)
    except FileNotFoundError as e:
        _print({"error": str(e)}, as_json=args.json)
        sys.exit(1)
    except RuntimeError as e:
        _print({"error": str(e)}, as_json=args.json)
        sys.exit(2)


if __name__ == "__main__":
    main()