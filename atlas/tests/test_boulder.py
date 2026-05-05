from pathlib import Path

from atlas.boulder import (
    Boulder,
    BoulderStatus,
    BoulderStore,
    Task,
    TaskStatus,
    Verification,
)


def test_boulder_lifecycle(tmp_path: Path) -> None:
    store = BoulderStore(tmp_path)
    b = Boulder(
        name="test-boulder",
        plan_path=str(tmp_path / "plan.md"),
        objective="Do the thing",
        tasks=[
            Task(id="t1", phase="Phase 1", title="First", description="", deliverable="", steps=["s1"]),
            Task(id="t2", phase="Phase 2", title="Second", description="", deliverable="", steps=["s1"]),
        ],
    )
    store.save(b)
    assert store.exists("test-boulder")

    loaded = store.load("test-boulder")
    assert loaded.name == "test-boulder"
    assert len(loaded.tasks) == 2
    assert loaded.tasks[0].status == TaskStatus.PENDING
    assert loaded.next_pending().id == "t1"

    loaded.tasks[0].status = TaskStatus.DONE
    loaded.tasks[1].status = TaskStatus.DONE
    assert loaded.is_done()
    loaded.status = BoulderStatus.DONE
    store.save(loaded)

    again = store.load("test-boulder")
    assert again.status == BoulderStatus.DONE
    assert again.next_pending() is None


def test_verification_roundtrip(tmp_path: Path) -> None:
    store = BoulderStore(tmp_path)
    b = Boulder(
        name="verif-test",
        plan_path="x",
        tasks=[
            Task(
                id="t1",
                phase="Phase 1",
                title="V",
                description="",
                deliverable="",
                steps=[],
                verifications=[Verification(command="pytest", description="run tests", passed=True, output="ok")],
            )
        ],
    )
    store.save(b)
    loaded = store.load("verif-test")
    assert loaded.tasks[0].verifications[0].command == "pytest"
    assert loaded.tasks[0].verifications[0].passed is True


def test_artifacts_rendered(tmp_path: Path) -> None:
    store = BoulderStore(tmp_path)
    b = Boulder(
        name="artifacts",
        plan_path="x",
        objective="Test artifacts",
        tasks=[Task(id="t1", phase="Phase 1", title="Hi", description="", deliverable="", steps=[])],
        findings=["found A"],
        decisions=["decided B"],
    )
    store.save(b)
    tl = store.task_list_path("artifacts").read_text()
    assert "Boulder: artifacts" in tl
    assert "t1" in tl
    np = store.notepad_path("artifacts").read_text()
    assert "found A" in np
    assert "decided B" in np


def test_list_all(tmp_path: Path) -> None:
    store = BoulderStore(tmp_path)
    for n in ["a", "b", "c"]:
        store.save(Boulder(name=n, plan_path="p", tasks=[Task(id="t", phase="P1", title="T", description="", deliverable="", steps=[])]))
    names = [b.name for b in store.list_all()]
    assert names == ["a", "b", "c"]
