class ASTLocker:
    """
    AST Namespace Locking Engine.
    Prevents parallel agents from modifying the same AST namespace concurrently.
    """
    def __init__(self):
        self.locked_namespaces = set()

    def acquire_lock(self, namespace: str) -> bool:
        if namespace in self.locked_namespaces:
            return False
        self.locked_namespaces.add(namespace)
        return True

    def release_lock(self, namespace: str):
        if namespace in self.locked_namespaces:
            self.locked_namespaces.remove(namespace)
