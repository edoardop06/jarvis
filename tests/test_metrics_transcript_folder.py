from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "vault_metrics.py"


def load_metrics():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("vault_metrics_folder_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TranscriptFolderTests(unittest.TestCase):
    """Token metrics must read the transcripts of the vault they run in,
    whatever the vault folder is called, not a hardcoded folder name."""

    def test_folder_name_follows_claude_code_rule(self):
        module = load_metrics()
        self.assertEqual(module.transcript_folder_name(Path("/Users/someone/Documents/My Vault")),
                         "-Users-someone-Documents-My-Vault")
        self.assertEqual(module.transcript_folder_name(Path("/home/a.b/vault_1")),
                         "-home-a-b-vault-1")

    def test_usage_counts_this_vault_transcripts(self):
        module = load_metrics()
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            vault = Path(directory) / "Any Name"
            vault.mkdir()
            folder = home / ".claude" / "projects" / module.transcript_folder_name(vault)
            folder.mkdir(parents=True)
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            line = {"type": "assistant", "timestamp": now,
                    "message": {"id": "m1", "usage": {"input_tokens": 3, "output_tokens": 5,
                                                      "cache_read_input_tokens": 7,
                                                      "cache_creation_input_tokens": 11}}}
            # The same answer on two lines counts once.
            (folder / "s.jsonl").write_text(json.dumps(line) + "\n" + json.dumps(line) + "\n", encoding="utf-8")
            setattr(module, "VAULT", vault)
            stats = module.usage_stats(home=home)
        self.assertEqual(stats["sessions"], 1)
        self.assertEqual(stats["total"], 26)


if __name__ == "__main__":
    unittest.main()
