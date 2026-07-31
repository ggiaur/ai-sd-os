from typing import List

from contracts.work_package import TaskItem
from kernel.swarm.ast_locker import ASTLocker


class SwarmOrchestrator:
    """Párhuzamosan futtatható feladatcsoportokra bontja egy WorkPackage
    taskjait. MVP szinten minden task saját, független csoportba kerül,
    mivel az AST-szintű ütközésfelismerés még nincs a taskok tartalmára
    kötve — ez a lock-infrastruktúrát biztosítja a jövőbeli bővítéshez."""

    def __init__(self) -> None:
        self.locker = ASTLocker()

    def partition_tasks(self, tasks: List[TaskItem]) -> List[List[TaskItem]]:
        groups: List[List[TaskItem]] = []
        sequential_group: List[TaskItem] = []

        for task in tasks:
            if self.locker.acquire_lock(task.requirement_ref, task.task_id):
                groups.append([task])
            else:
                # Namespace already locked by another task in this batch: it
                # cannot run in parallel, but it must still be scheduled.
                # Previously a failed lock silently dropped the task from the
                # execution plan entirely instead of queuing it.
                sequential_group.append(task)

        if sequential_group:
            groups.append(sequential_group)

        return groups
