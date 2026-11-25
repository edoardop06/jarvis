from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "vault_lint.py"


def load_vault_lint():
    spec = importlib.util.spec_from_file_location("vault_lint_build_output", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildOutputTests(unittest.TestCase):
    """A code package built inside the vault downloads its dependencies into
    `.build/`, Markdown files and AGENTS.md included. That folder is rebuilt by
    the compiler and is not the owner's notes: the lint must not count it."""

    def test_build_folder_is_not_scanned(self):
        module = load_vault_lint()
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            (vault / "Maps & Manuals").mkdir(parents=True)
            (vault / "Note.md").write_text("# Note\n", encoding="utf-8")
            deps = vault / "Skills" / "app" / ".build" / "checkouts" / "lib"
            deps.mkdir(parents=True)
            (deps / "README.md").write_text("# Someone else's readme\n", encoding="utf-8")
            (deps / "AGENTS.md").write_text("# Someone else's rules\n", encoding="utf-8")
            module.VAULT = vault
            module.SYSTEM = vault / "System"

            rels = {str(f.relative_to(vault)) for f in module.get_all_md_files()}
            self.assertIn("Note.md", rels)
            self.assertFalse(any(".build" in r for r in rels), rels)


if __name__ == "__main__":
    unittest.main()
