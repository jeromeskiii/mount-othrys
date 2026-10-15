from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from coeus import __version__
from coeus.consultant import Consultant, apply_inquiry_step
from coeus.llm import CoeusLLM, LLMConfig
from coeus.state import Draft, DraftStore, Phase, QA


_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _slugify(text: str, max_len: int = 40) -> str:
    s = text.lower().strip()
    s = _SLUG_RE.sub("-", s).strip("-")
    return s[:max_len] or "draft"


def _store(args: argparse.Namespace) -> DraftStore:
    return DraftStore(Path(args.root).resolve())


def _llm(args: argparse.Namespace) -> CoeusLLM:
    return CoeusLLM(LLMConfig(model=args.model, api_key=args.api_key))


def _emit(args: argparse.Namespace, payload: dict, human: str) -> None:
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(human)


def cmd_interview(args: argparse.Namespace) -> int:
    store = _store(args)
    name = args.name or _slugify(args.request)
    if store.exists(name) and not args.force:
        print(f"Draft '{name}' already exists. Use 'coeus continue {name}' or pass --force.", file=sys.stderr)
        return 2
    draft = Draft(name=name, request=args.request)
    store.save(draft)

    if args.no_ask:
        _emit(
            args,
            {"name": name, "phase": draft.phase.value, "draft": str(store.draft_path(name))},
            f"Created draft '{name}' at {store.draft_path(name)}\nNext: coeus ask {name}",
        )
        return 0
    return _ask_loop(args, store, draft)


def cmd_continue(args: argparse.Namespace) -> int:
    store = _store(args)
    draft = store.load(args.name)
    return _ask_loop(args, store, draft)


def cmd_ask(args: argparse.Namespace) -> int:
    store = _store(args)
    draft = store.load(args.name)
    if draft.phase != Phase.INQUIRY:
        print(f"Draft '{args.name}' is in phase '{draft.phase.value}', not inquiry.", file=sys.stderr)
        return 2

    consultant = Consultant(_llm(args))
    step = consultant.next_inquiry_step(draft)

    if step.action == "ask":
        apply_inquiry_step(draft, step)
        store.save(draft)
        _emit(
            args,
            {"action": "ask", "gate": step.gate, "question": step.question, "name": draft.name},
            f"[{step.gate}]\nQ: {step.question}\n\nAnswer with: coeus answer {draft.name} \"<your answer>\"",
        )
        return 0
    if step.action == "clear":
        apply_inquiry_step(draft, step)
        store.save(draft)
        _emit(
            args,
            {"action": "clear", "gate": step.gate, "finding": step.finding, "pending": draft.pending_gates()},
            f"Gate cleared: {step.gate}\nFinding: {step.finding}\nPending gates: {', '.join(draft.pending_gates()) or '(none)'}",
        )
        return 0
    if step.action == "ready_for_plan":
        apply_inquiry_step(draft, step)
        store.save(draft)
        _emit(
            args,
            {"action": "ready_for_plan", "summary": step.summary, "name": draft.name},
            f"All gates cleared.\nSummary: {step.summary}\n\nNext: coeus plan {draft.name}",
        )
        return 0
    print(f"Unknown action from Coeus: {step.action}", file=sys.stderr)
    return 1


def cmd_answer(args: argparse.Namespace) -> int:
    store = _store(args)
    draft = store.load(args.name)
    unanswered = [qa for qa in draft.qa_log if qa.answer is None]
    if not unanswered:
        print("No pending question. Run: coeus ask " + args.name, file=sys.stderr)
        return 2
    from datetime import datetime, timezone

    unanswered[-1].answer = args.answer
    unanswered[-1].answered_at = datetime.now(timezone.utc).isoformat()
    store.save(draft)

    if args.no_advance:
        _emit(args, {"name": draft.name, "answered": True}, "Answer recorded.")
        return 0
    return cmd_ask(args)


def _ask_loop(args: argparse.Namespace, store: DraftStore, draft: Draft) -> int:
    consultant = Consultant(_llm(args))
    if not sys.stdin.isatty():
        _emit(
            args,
            {"name": draft.name, "phase": draft.phase.value, "draft": str(store.draft_path(draft.name)), "status": "draft_created"},
            f"Draft '{draft.name}' created at {store.draft_path(draft.name)}. Interactive ask-loop requires a TTY. Use 'coeus ask {draft.name}' or 'coeus continue {draft.name}' for scripted use.",
        )
        return 0
    while draft.phase == Phase.INQUIRY:
        step = consultant.next_inquiry_step(draft)
        if step.action == "ask":
            apply_inquiry_step(draft, step)
            store.save(draft)
            print(f"\n[{step.gate}]\nQ: {step.question}")
            try:
                answer = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nInterview paused. Resume with: coeus continue " + draft.name)
                return 0
            if not answer:
                print("Empty answer; pausing. Resume with: coeus continue " + draft.name)
                return 0
            from datetime import datetime, timezone

            draft.qa_log[-1].answer = answer
            draft.qa_log[-1].answered_at = datetime.now(timezone.utc).isoformat()
            store.save(draft)
        elif step.action == "clear":
            apply_inquiry_step(draft, step)
            store.save(draft)
            print(f"  ✓ {step.gate}: {step.finding}")
        elif step.action == "ready_for_plan":
            apply_inquiry_step(draft, step)
            store.save(draft)
            print(f"\nAll gates cleared.\nSummary: {step.summary}")
            print(f"\nNext: coeus plan {draft.name}")
            return 0
        else:
            print(f"Unknown action: {step.action}", file=sys.stderr)
            return 1
    print(f"Draft now in phase '{draft.phase.value}'. Next: coeus plan {draft.name}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    store = _store(args)
    draft = store.load(args.name)
    payload = {
        "name": draft.name,
        "phase": draft.phase.value,
        "request": draft.request,
        "clearance": draft.clearance,
        "pending_gates": draft.pending_gates(),
        "qa_count": len(draft.qa_log),
        "unanswered": sum(1 for qa in draft.qa_log if qa.answer is None),
        "draft_path": str(store.draft_path(draft.name)),
        "plan_path": draft.plan_path,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    print(f"Draft: {draft.name}")
    print(f"Phase: {draft.phase.value}")
    print(f"Q&A:   {payload['qa_count']} ({payload['unanswered']} unanswered)")
    print("Gates:")
    for g, ok in draft.clearance.items():
        print(f"  {'[x]' if ok else '[ ]'} {g}")
    print(f"Draft file: {payload['draft_path']}")
    if draft.plan_path:
        print(f"Plan file:  {draft.plan_path}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = _store(args)
    drafts = store.list_all()
    if args.json:
        print(json.dumps(
            [{"name": d.name, "phase": d.phase.value, "request": d.request, "updated_at": d.updated_at} for d in drafts],
            indent=2,
        ))
        return 0
    if not drafts:
        print("No drafts yet. Start one: coeus interview \"<request>\"")
        return 0
    for d in drafts:
        print(f"  {d.name:30s} {d.phase.value:18s} {d.request[:60]}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    store = _store(args)
    target = args.target or "draft"
    draft = store.load(args.name)
    if target == "draft":
        path = store.draft_path(draft.name)
    elif target == "plan":
        if not draft.plan_path:
            print("No plan generated yet. Run: coeus plan " + draft.name, file=sys.stderr)
            return 2
        path = Path(draft.plan_path)
    else:
        print(f"Unknown target: {target}", file=sys.stderr)
        return 2
    print(path.read_text())
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    store = _store(args)
    draft = store.load(args.name)
    if not draft.is_cleared() and not args.force:
        print(
            f"Cannot plan: gates still open: {', '.join(draft.pending_gates())}\n"
            f"Continue inquiry with: coeus continue {draft.name}\n"
            f"Or override with --force.",
            file=sys.stderr,
        )
        return 2

    consultant = Consultant(_llm(args))

    if not args.skip_metis:
        print("Running Metis pre-plan critique…", file=sys.stderr)
        metis_text, proceed = consultant.metis_review(draft)
        draft.metis_notes = metis_text
        if not proceed and not args.force:
            draft.phase = Phase.INQUIRY
            store.save(draft)
            print("\nMetis verdict: NEEDS_MORE_INQUIRY\n", file=sys.stderr)
            print(metis_text)
            print(f"\nDraft reverted to inquiry. Continue with: coeus continue {draft.name}", file=sys.stderr)
            return 3
        store.save(draft)

    print("Generating plan…", file=sys.stderr)
    draft.phase = Phase.PLAN_GENERATION
    plan_md = consultant.generate_plan(draft)
    plan_path = store.plan_path(draft.name)
    plan_path.write_text(plan_md)
    draft.plan_path = str(plan_path)
    draft.phase = Phase.COMPLETE
    store.save(draft)

    _emit(
        args,
        {"name": draft.name, "plan_path": str(plan_path), "phase": draft.phase.value},
        f"Plan written: {plan_path}\n\nReview with Momus: coeus review {draft.name}",
    )
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    store = _store(args)
    draft = store.load(args.name)
    if not draft.plan_path:
        print(f"No plan to review. Run: coeus plan {args.name}", file=sys.stderr)
        return 2
    plan_md = Path(draft.plan_path).read_text()
    consultant = Consultant(_llm(args))
    print("Running Momus review…", file=sys.stderr)
    review_text, approved = consultant.momus_review(plan_md)
    draft.momus_notes = review_text
    draft.phase = Phase.MOMUS_REVIEW if not approved else Phase.COMPLETE
    store.save(draft)

    _emit(
        args,
        {"name": draft.name, "approved": approved, "review": review_text},
        review_text + f"\n\n{'✅ Approved' if approved else '⚠️  Revisions required — regenerate plan with corrections.'}",
    )
    return 0


def cmd_manifest(args: argparse.Namespace) -> int:
    store = _store(args)
    draft = store.load(args.name)
    if not draft.plan_path:
        print(f"No plan found for {args.name}. Run 'coeus plan {args.name}' first.", file=sys.stderr)
        return 2

    plan_md = Path(draft.plan_path).read_text()

    # Phase 3: Formal Handshake Protocol
    # Use LLM to extract structured tasks from the markdown plan
    prompt = f"Convert this markdown plan into a structured JSON manifest for an orchestrator.\n\nPlan:\n{plan_md}"

    consultant = Consultant(_llm(args))
    raw = consultant.llm.call(
        system="You are a Manifest Architect. Extract a JSON list of tasks with: id, title, description, deliverable, and priority (1-5).",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )

    from coeus.consultant import _extract_json
    try:
        manifest_data = _extract_json(raw)
        out_path = Path(draft.plan_path).with_suffix(".manifest.json")

        # Integration: Seed Fortress Store (shared blackboard)
        try:
            db_path = Path.home() / ".sisyphus" / "fortress.db"
            from kronos.storage import FortressStore
            fortress = FortressStore(db_path)
            cid = fortress.create_campaign(draft.request, lead_titan="coeus")
            for finding in draft.findings:
                fortress.store_finding(cid, "initial_finding", finding, "coeus")
            manifest_data["campaign_id"] = cid
        except ImportError:
            pass

        out_path.write_text(json.dumps(manifest_data, indent=2))
        _emit(args, manifest_data, f"Manifest generated: {out_path}")
        return 0
    except Exception as e:
        print(f"Failed to parse manifest: {e}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="coeus",
        description="Coeus — Strategic Planning Consultant. Interview-first planning with Metis & Momus review.",
    )
    p.add_argument("--version", action="version", version=f"coeus {__version__}")
    p.add_argument("--root", default=".", help="Project root (default: cwd). Drafts live under <root>/.sisyphus/")
    p.add_argument("--model", default="claude-opus-4-5", help="Anthropic model id")
    p.add_argument("--api-key", default=None, help="Anthropic API key (else uses ANTHROPIC_API_KEY)")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON for agent integration")

    sub = p.add_subparsers(dest="command", required=True)

    i = sub.add_parser("interview", help="Start a new interview")
    i.add_argument("request", help="The user's request, in quotes")
    i.add_argument("--name", help="Draft name (slug). Auto-derived from request if omitted.")
    i.add_argument("--force", action="store_true", help="Overwrite existing draft of same name")
    i.add_argument("--no-ask", action="store_true", help="Create draft only; do not begin interactive Q&A")
    i.set_defaults(func=cmd_interview)

    c = sub.add_parser("continue", help="Resume interactive Q&A on an existing draft")
    c.add_argument("name")
    c.set_defaults(func=cmd_continue)

    a = sub.add_parser("ask", help="Generate the next interview action (one step, scripted use)")
    a.add_argument("name")
    a.set_defaults(func=cmd_ask)

    ans = sub.add_parser("answer", help="Record an answer to the latest open question")
    ans.add_argument("name")
    ans.add_argument("answer")
    ans.add_argument("--no-advance", action="store_true", help="Record answer without auto-running next ask step")
    ans.set_defaults(func=cmd_answer)

    s = sub.add_parser("status", help="Show clearance gates and progress for a draft")
    s.add_argument("name")
    s.set_defaults(func=cmd_status)

    ls = sub.add_parser("list", help="List all drafts")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="Print the rendered draft or plan markdown")
    sh.add_argument("name")
    sh.add_argument("target", nargs="?", choices=["draft", "plan"], default="draft")
    sh.set_defaults(func=cmd_show)

    pl = sub.add_parser("plan", help="Generate the work plan (Phase 2). Runs Metis review unless --skip-metis.")
    pl.add_argument("name")
    pl.add_argument("--skip-metis", action="store_true")
    pl.add_argument("--force", action="store_true", help="Override open clearance gates / Metis veto")
    pl.set_defaults(func=cmd_plan)

    r = sub.add_parser("review", help="Run Momus review on the generated plan")
    r.add_argument("name")
    r.set_defaults(func=cmd_review)

    m = sub.add_parser("manifest", help="Generate a structured JSON manifest for Atlas")
    m.add_argument("name")
    m.set_defaults(func=cmd_manifest)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
