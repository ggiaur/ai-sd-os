from kernel.swarm.ast_locker import ASTLocker
from kernel.swarm.orchestrator import SwarmOrchestrator
from contracts.work_package import TaskItem


def test_ast_locker_acquire_and_release():
    locker = ASTLocker()
    assert locker.acquire_lock("src/app.py", "TASK-001") is True
    assert locker.acquire_lock("src/app.py", "TASK-001") is False  # already locked
    assert locker.acquire_lock("src/app.py", "TASK-002") is True  # different node, ok

    locker.release_lock("src/app.py", "TASK-001")
    assert locker.acquire_lock("src/app.py", "TASK-001") is True


def test_swarm_orchestrator_partitions_tasks():
    tasks = [
        TaskItem(task_id="TASK-001", description="desc 1", requirement_ref="FR-001"),
        TaskItem(task_id="TASK-002", description="desc 2", requirement_ref="FR-002"),
    ]
    orchestrator = SwarmOrchestrator()
    groups = orchestrator.partition_tasks(tasks)

    assert len(groups) == 2
    assert groups[0][0].task_id == "TASK-001"
    assert groups[1][0].task_id == "TASK-002"
