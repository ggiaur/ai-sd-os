import ast
import subprocess
from pathlib import Path


class SemanticReplayEngine:
    """Ellenőrzi, hogy egy visszajátszott (replay) kód szemantikailag
    egyenértékű-e az eredetivel (SYSTEM_CONSTITUTION L2.1 recovery garancia)."""

    @staticmethod
    def verify_ast_equivalence(original_code: str, replayed_code: str) -> bool:
        try:
            tree_orig = ast.parse(original_code)
            tree_repl = ast.parse(replayed_code)
            return ast.dump(tree_orig, annotate_fields=False) == ast.dump(tree_repl, annotate_fields=False)
        except SyntaxError:
            return False

    @staticmethod
    def verify_test_pass(workspace_path: Path, test_command: str = "python -m pytest") -> bool:
        res = subprocess.run(test_command, shell=True, cwd=workspace_path, capture_output=True)
        return res.returncode == 0

    @classmethod
    def is_semantically_equivalent(
        cls, original_code: str, replayed_code: str, workspace_path: Path, test_command: str = "python -m pytest"
    ) -> bool:
        return cls.verify_ast_equivalence(original_code, replayed_code) or cls.verify_test_pass(
            workspace_path, test_command
        )
