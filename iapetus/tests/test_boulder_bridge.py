from pathlib import Path

from atlas.boulder import Boulder, Task, TaskStatus, BoulderStatus, Verification

from iapetus.boulder_bridge import (
    find_blocked_tasks,
    find_next_pending,
    to_objective,
)


def test_find_blocked_and_pending() -> None:
    b = Boulder(
        name="b",
        plan_path="p",
        tasks=[
            Task(id="t1", phase="P1", title="T1", description="", deliverable="", steps=[], status=TaskStatus.BLOCKED),
            Task(id="t2", phase="P2", title="T2", description="", deliverable="", steps=[], status=TaskStatus.PENDING),
            Task(id="t3", phase="P3", title="T3", description="", deliverable="", steps=[], status=TaskStatus.DONE),
        ],
    )
    blocked = find_blocked_tasks(b)
    assert len(blocked) == 1 and blocked[0].id == "t1"
    pending = find_next_pending(b)
    assert pending is not None and pending.id == "t2"


def test_to_objective_includes_task_details() -> None:
    b = Boulder(
        name="deep",
        plan_path="p",
        objective="Refactor auth system",
        tasks=[
            Task(
                id="t1",
                phase="P1",
                title="Split auth module",
                description="Break monolith into services",
                deliverable="Two files",
                steps=["Read auth.py", "Split"],
                verifications=[Verification(command="pytest", description="run tests")],
            )
        ],
        findings=["found pattern X"],
        decisions=["use JWT"],
    )
    obj = to_objective(boulder=b, task=b.tasks[0])
    assert "Refactor auth system" in obj
    assert "Split auth module" in obj
    assert "Break monolith into services" in obj
    assert "Read auth.py" in obj
    assert "pytest" in obj
    assert "found pattern X" in obj
    assert "use JWT" in obj
