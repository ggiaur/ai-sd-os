from typing import Dict, Set


class ASTLocker:
    """AST namespace-szintű zárolás párhuzamos ágensek számára, hogy két
    ágens ne módosíthassa ütközően ugyanazt a kódrészletet egyidejűleg."""

    def __init__(self) -> None:
        self._locks: Dict[str, Set[str]] = {}  # filepath -> set of node_ids

    def acquire_lock(self, filepath: str, node_id: str) -> bool:
        held = self._locks.setdefault(filepath, set())
        if node_id in held:
            return False
        held.add(node_id)
        return True

    def release_lock(self, filepath: str, node_id: str) -> None:
        held = self._locks.get(filepath)
        if held and node_id in held:
            held.remove(node_id)

    def is_locked(self, filepath: str, node_id: str) -> bool:
        return node_id in self._locks.get(filepath, set())
