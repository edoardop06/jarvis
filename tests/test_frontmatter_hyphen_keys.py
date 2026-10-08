from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "vault_lint.py"


def load_vault_lint():
    spec = importlib.util.spec_from_file_location("vault_lint_hyphen_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FrontmatterHyphenKeyTests(unittest.TestCase):
    def check(self, block):
        module = load_vault_lint()
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            note = vault / "SKILL.md"
            note.write_text(f"---\n{block}---\n\n# Skill\n", encoding="utf-8")
            setattr(module, "VAULT", vault)
            return module.check_frontmatter_parses([note])

    def test_skill_settings_with_hyphens_are_settings(self):
        # Agent Skills frontmatter uses keys such as allowed-tools and
        # disable-model-invocation; they are valid YAML settings.
        block = (
            "name: example\n"
            "description: >\n"
            "  Folded text.\n"
            "disable-model-invocation: true\n"
            "argument-hint: \"[lite|full]\"\n"
            "allowed-tools: Read\n"
        )
        self.assertEqual(self.check(block), [])

    def test_a_stray_line_is_still_reported(self):
        self.assertEqual(len(self.check("name: example\nnot a setting\n")), 1)


if __name__ == "__main__":
    unittest.main()
