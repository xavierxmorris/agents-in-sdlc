import ast
import unittest
from pathlib import Path
from typing import List, Tuple


class TestDocstringCoverage(unittest.TestCase):
    MODULE_PATHS: List[Path] = [
        Path(__file__).resolve().parents[1] / "models" / "base.py",
        Path(__file__).resolve().parents[1] / "models" / "publisher.py",
        Path(__file__).resolve().parents[1] / "models" / "category.py",
        Path(__file__).resolve().parents[1] / "models" / "game.py",
        Path(__file__).resolve().parents[1] / "routes" / "games.py",
        Path(__file__).resolve().parents[1] / "utils" / "seed_database.py",
    ]

    @staticmethod
    def _missing_docstrings(module_path: Path) -> List[Tuple[int, str]]:
        """Return all functions and methods in a module that are missing docstrings."""
        module_tree = ast.parse(module_path.read_text(encoding="utf-8"))
        return sorted(
            (
                node.lineno,
                node.name,
            )
            for node in ast.walk(module_tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and ast.get_docstring(node) is None
        )

    def test_docstrings_present_in_target_modules(self) -> None:
        """Ensure all functions and methods in target modules include docstrings."""
        missing_by_module = {
            str(module_path): self._missing_docstrings(module_path)
            for module_path in self.MODULE_PATHS
        }
        missing = {
            module: missing_functions
            for module, missing_functions in missing_by_module.items()
            if missing_functions
        }
        self.assertEqual(missing, {})


if __name__ == "__main__":
    unittest.main()
