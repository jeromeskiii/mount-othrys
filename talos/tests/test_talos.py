from talos.classifier import classify, RequestType


def test_trivial_classification():
    rtype, reason = classify("fix the typo in auth.py")
    assert rtype == RequestType.TRIVIAL


def test_explicit_classification():
    rtype, reason = classify("change the add function at line 42 in app/main.py")
    assert rtype == RequestType.EXPLICIT


def test_exploratory_classification():
    rtype, reason = classify("how does the auth middleware work?")
    assert rtype == RequestType.EXPLORATORY


def test_open_ended_classification():
    rtype, reason = classify("refactor the entire auth module")
    assert rtype == RequestType.OPEN_ENDED


def test_ambiguous_classification():
    rtype, reason = classify("maybe add caching? or maybe not, I'm not sure")
    assert rtype == RequestType.AMBIGUOUS


def test_multi_signal_explicit_wins():
    rtype, reason = classify("change line 42 in auth.py and add caching to the login handler")
    assert rtype == RequestType.EXPLICIT


def test_delegation_prompt_structure():
    from talos.delegation import build_delegation_prompt
    prompt = build_delegation_prompt(
        task="Add healthz endpoint",
        outcome="Working /healthz route",
        tools=["bash", "read", "edit"],
        must_do=["Add endpoint to main.py", "Run tests"],
        must_not=["Delete existing code", "Modify unrelated files"],
        context="FastAPI app at /tmp/smoke",
    )
    assert "1. TASK:" in prompt
    assert "2. EXPECTED OUTCOME:" in prompt
    assert "3. REQUIRED TOOLS:" in prompt
    assert "4. MUST DO:" in prompt
    assert "5. MUST NOT DO:" in prompt
    assert "6. CONTEXT:" in prompt
    assert "Add healthz endpoint" in prompt
    assert "FastAPI app at /tmp/smoke" in prompt


def test_session_create_and_load():
    from talos.session import create_session, load_session, delete_session, list_sessions
    import time
    s = create_session(titan="coeus", objective="test plan")
    assert s.session_id.startswith("session_")
    assert s.titan == "coeus"
    assert s.objective == "test plan"
    assert s.status == "active"

    loaded = load_session(s.session_id)
    assert loaded is not None
    assert loaded.session_id == s.session_id

    all_sessions = list_sessions()
    assert any(sess.session_id == s.session_id for sess in all_sessions)

    delete_session(s.session_id)
    assert load_session(s.session_id) is None


def test_orchestrator_todo_lifecycle():
    from talos.orchestrator import TalosOrchestrator, TodoStatus
    from pathlib import Path
    orch = TalosOrchestrator(Path("/tmp"))
    t = orch.add("Implement auth", titan="iapetus")
    assert t.id == "todo-001"
    assert t.status == TodoStatus.PENDING

    orch.in_progress(t.id)
    assert orch.todos[0].status == TodoStatus.IN_PROGRESS

    orch.complete(t.id, notes=["done!"])
    assert orch.todos[0].status == TodoStatus.DONE
    assert "done!" in orch.todos[0].notes

    assert orch.is_done()


def test_titan_router_plan():
    from talos.titan_router import route_request, TITAN_COEUS
    r = route_request("plan this feature for me")
    assert r.titan == TITAN_COEUS
    assert r.subcommand == "interview"


def test_titan_router_plan_reason():
    from talos.titan_router import route_request
    r = route_request("help me think through this feature")
    assert r.reason == "Planning request detected"


def test_titan_router_atlas():
    from talos.titan_router import route_request, TITAN_ATLAS
    r = route_request("run the atlas boulder")
    assert r.titan == TITAN_ATLAS


def test_titan_router_iapetus():
    from talos.titan_router import route_request, TITAN_IAPETUS
    r = route_request("deep analyze the codebase")
    assert r.titan == TITAN_IAPETUS


def test_titan_router_direct():
    from talos.titan_router import route_request, TITAN_DIRECT
    r = route_request("fix the bug in main.py")
    assert r.titan == TITAN_DIRECT
