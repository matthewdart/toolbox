import json
import tempfile
import unittest
from pathlib import Path

from adapters.openai.toolgen import main as toolgen_main


class ToolgenTests(unittest.TestCase):
    def test_toolgen_creates_text_normalize(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            toolgen_main_args = ["--out-dir", tmpdir]
            toolgen_main(toolgen_main_args)

            tool_path = Path(tmpdir) / "text.normalize_markdown.json"
            self.assertTrue(tool_path.exists())
            data = json.loads(tool_path.read_text(encoding="utf-8"))
            self.assertEqual(data["type"], "function")
            self.assertEqual(data["function"]["name"], "text.normalize_markdown")
            self.assertIn("parameters", data["function"])


if __name__ == "__main__":
    unittest.main()
