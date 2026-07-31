from kernel.swarm.ast_locker import ASTLocker
from kernel.swarm.orchestrator import SwarmOrchestrator
from contracts.work_package import TaskItem


# --- ASTLocker --------------------------------------------------------

def test_ast_locker_is_locked_reflects_acquire_and_release():
    locker = ASTLocker()
    assert locker.is_locked("src/app.py", "TASK-001") is False

    locker.acquire_lock("src/app.py", "TASK-001")
    assert locker.is_locked("src/app.py", "TASK-001") is True

    locker.release_lock("src/app.py", "TASK-001")
    assert locker.is_locked("src/app.py", "TASK-001") is False


def test_ast_locker_different_files_are_independent():
    locker = ASTLocker()
    assert locker.acquire_lock("src/a.py", "TASK-001") is True
    assert locker.acquire_lock("src/b.py", "TASK-001") is True  # same node id, different file — fine


# --- SwarmOrchestrator ---------------------------------------------------

def _task(task_id, req_ref):
    return TaskItem(
        task_id=task_id, description="d", requirement_ref=req_ref, expected_output=f"{req_ref}-DONE"
    )


def test_partition_tasks_never_drops_a_task_on_lock_conflict():
    """Regression: a task whose namespace is already locked used to vanish
    from the execution plan entirely instead of being scheduled sequentially.
    """
    tasks = [
        _task("TASK-001", "FR-001"),
        _task("TASK-002", "FR-001"),  # same requirement_ref -> lock conflict
        _task("TASK-003", "FR-002"),
    ]

    orchestrator = SwarmOrchestrator()
    groups = orchestrator.partition_tasks(tasks)

    all_scheduled = [t.task_id for group in groups for t in group]
    assert sorted(all_scheduled) == ["TASK-001", "TASK-002", "TASK-003"]


def test_partition_tasks_puts_independent_tasks_in_their_own_group():
    tasks = [_task("TASK-001", "FR-001"), _task("TASK-002", "FR-002")]

    orchestrator = SwarmOrchestrator()
    groups = orchestrator.partition_tasks(tasks)

    assert len(groups) == 2
    assert all(len(g) == 1 for g in groups)
