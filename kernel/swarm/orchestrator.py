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
        for task in tasks:
            if self.locker.acquire_lock(task.requirement_ref, task.task_id):
                groups.append([task])
        return groups
